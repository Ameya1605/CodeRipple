import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.core.logging_config import configure_logging
from backend.config import validate_config

# Fix #1: Configure structured logging BEFORE anything else
configure_logging()
logger = logging.getLogger(__name__)

# F-8: Validate config at startup (warns in dev, crashes in prod)
validate_config()

from backend.indexer.vector_store import vector_store
from backend.graph.neo4j_client import neo4j_client
from backend.api import repos, analyze, health, symbols, graph, feedback, webhooks, indexer
from backend.jobs.tasks import redis_client
from backend.query.prompt_builder import build_query_prompt
from backend.query.llm_client import call_llm_streaming
from backend.query.response_validator import validate_response
from backend.retrieval.retriever import retrieve_dependents, build_call_graph_summary
from backend.indexer.schema import CodeChunk


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up FastAPI. Initializing collections and constraints...")

    # Fix #2: Startup Redis connectivity check
    try:
        import redis.asyncio as aioredis
        from backend.config import REDIS_URL
        r = aioredis.from_url(REDIS_URL, socket_connect_timeout=3)
        await r.ping()
        await r.aclose()
        logger.info(f"Redis connected: {REDIS_URL}")
    except Exception as e:
        logger.warning(
            f"Redis unreachable at {REDIS_URL}. "
            f"Run: docker compose up redis -d   OR set REDIS_URL in .env. "
            f"Error: {e}"
        )

    try:
        await vector_store.init_collections()
        await neo4j_client.create_constraints()
    except Exception as e:
        logger.error(f"Startup initialization failed (ignoring for tests): {e}")
    yield
    logger.info("Shutting down FastAPI. Closing connections...")
    await neo4j_client.close()

app = FastAPI(title="Dependency Impact Analyzer", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

UNPROTECTED_PATHS = {"/api/v1/health/codebase", "/api/v1/analyze/health", "/api/health", "/docs", "/openapi.json"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in UNPROTECTED_PATHS:
            return await call_next(request)
        if request.url.path.startswith("/ws/"):
            return await call_next(request)
        # Auth logic is actually inside Dependencies as it uses Depends(). We just passthrough here.
        return await call_next(request)

app.add_middleware(AuthMiddleware)


app.include_router(repos.router)
app.include_router(analyze.router)
app.include_router(health.router)
app.include_router(symbols.router)
app.include_router(graph.router)
app.include_router(feedback.router)
app.include_router(webhooks.router)
app.include_router(indexer.router)

@app.get("/")
async def root():
    return {
        "name": "Dependency Impact Analyzer",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health/codebase",
        "status": "running"
    }

async def ws_auth():
    return {"user_id": "test"}

@app.websocket("/ws/index/{job_id}")
async def stream_index_progress(ws: WebSocket, job_id: str):
    await ws.accept()
    if not redis_client:
        await ws.send_json({"type": "error", "message": "Redis not configured"})
        await ws.close()
        return
        
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"index_progress:{job_id}")
    try:
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = json.loads(message["data"])
                await ws.send_json({"type": "progress", "data": data})
                if data.get("status") in ["completed", "failed", "success"]:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        pubsub.unsubscribe()
        pubsub.close()

from backend.api import ws
app.include_router(ws.router)
