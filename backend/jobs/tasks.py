"""
Celery tasks for analysis and indexing.

Fix #1:  Added missing logger import.
Fix #9:  Uses WSEventType constants instead of raw strings.
Fix #10: Uses Redis-backed context_store instead of in-process fallback_store.
Fix #12: Uses _run_async() helper + sync Redis _publish() to avoid event loop fragility.
"""
import asyncio
import json
import logging
import sys
import redis as sync_redis
from backend.config import REDIS_URL
from backend.indexer.pipeline import run_indexing
from backend.jobs.celery_app import celery_app
from backend.core.events import WSEventType

# Fix #1: Define logger — was missing, caused NameError on every failed analysis
logger = logging.getLogger(__name__)

try:
    redis_client = sync_redis.Redis.from_url(REDIS_URL)
except Exception:
    redis_client = None


def _get_channel_key(task_id: str) -> str:
    """Must match the channel format in websocket.py."""
    return f"dia:analysis:progress:{task_id}"


def _publish(task_id: str, event: dict) -> None:
    """
    Fix #12: Publish a WebSocket event from a sync Celery task context.
    Uses the synchronous Redis client — no event loop management needed.
    """
    try:
        r = sync_redis.from_url(REDIS_URL, decode_responses=True)
        channel = _get_channel_key(task_id)
        r.publish(channel, json.dumps(event))
        r.close()
    except Exception as e:
        # Never let a publish failure crash the analysis task
        logger.warning(f"Publish to {task_id} failed: {e}")


def _run_async(coro):
    """
    Fix #12: Safely run a coroutine from a synchronous Celery task.
    Handles Windows ProactorEventLoop requirement and already-running loops.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed loop")
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery_app.task(bind=True)
def run_index_task(self, repo_root: str, repo_id: str, url: str = None):
    job_id = self.request.id
    if redis_client:
        redis_client.publish(f"index_progress:{job_id}", json.dumps({"status": "started", "progress": 0}))
    
    try:
        if url:
            import subprocess
            import shutil
            import os
            if os.path.exists(repo_root):
                shutil.rmtree(repo_root)
            subprocess.run(["git", "clone", url, repo_root], check=True)

        chunks = _run_async(run_indexing(repo_root, repo_id, full=True))
        
        if redis_client:
            redis_client.publish(f"index_progress:{job_id}", json.dumps({"status": "completed", "progress": 100, "chunks": len(chunks)}))
        return {"status": "success", "chunks": len(chunks)}
    except Exception as e:
        if redis_client:
            redis_client.publish(f"index_progress:{job_id}", json.dumps({"status": "failed", "error": str(e)}))
        raise e


@celery_app.task(bind=True, max_retries=3)
def run_analysis(self, request_id: str, repo_id: str, target: str):
    task_id = self.request.id
    
    _publish(task_id, {"type": WSEventType.PROGRESS, "step": "retrieval", "pct": 10, "message": "Starting analysis task..."})
    
    try:
        # Fix #10: Load context from Redis-backed store instead of in-process fallback
        from backend.core.context_store import load_context
        
        ctx_data = _run_async(load_context(request_id))
            
        if not ctx_data:
            err = f"Analysis context for {request_id} not found or expired in Redis"
            logger.error(err)
            _publish(task_id, {"type": WSEventType.ERROR, "message": err})
            return
        
        from backend.indexer.schema import CodeChunk
        from backend.retrieval.retriever import retrieve_dependents, build_call_graph_summary, get_symbol_by_qname
        from backend.query.prompt_builder import build_query_prompt
        from backend.query.llm_client import call_llm_streaming
        from backend.query.response_validator import validate_response
        from backend.intelligence.cdl.differ import contract_differ
        from backend.intelligence.cdl.schema import SymbolContract
        from backend.intelligence.ownership import ownership_analyzer
            
        changed_symbol = CodeChunk(**ctx_data["changed_symbol"])
        change_summary = ctx_data["change_summary"]
        
        _publish(task_id, {"type": WSEventType.PROGRESS, "step": "retrieval", "pct": 20, "message": "Retrieving dependents..."})
        retrieved = _run_async(retrieve_dependents(changed_symbol))
        
        _publish(task_id, {"type": WSEventType.PROGRESS, "step": "grounded_context", "pct": 40, "message": "Building graph summary..."})
        graph_summary = _run_async(build_call_graph_summary(changed_symbol.qualified_name, changed_symbol.repo_id))
        
        if "nodes" in graph_summary and "edges" in graph_summary:
            _publish(task_id, {"type": WSEventType.GRAPH_DATA, "nodes": graph_summary["nodes"], "edges": graph_summary["edges"]})
        
        _publish(task_id, {"type": WSEventType.PROGRESS, "step": "cdl_diff", "pct": 60, "message": "Running deterministic contract check..."})
        old_symbol = _run_async(get_symbol_by_qname(changed_symbol.qualified_name, changed_symbol.repo_id))
        cdl_delta = None
        if old_symbol and old_symbol.contract_data and changed_symbol.contract_data:
            try:
                old_contract = SymbolContract(**old_symbol.contract_data)
                new_contract = SymbolContract(**changed_symbol.contract_data)
                cdl_delta = contract_differ.diff(old_contract, new_contract)
                _publish(task_id, {
                    "type": WSEventType.CDL_DELTA, 
                    "is_breaking": cdl_delta.is_breaking,
                    "semver": cdl_delta.semver_suggestion,
                    "changes": [c.value for c in cdl_delta.changes]
                })
            except Exception:
                pass
                
        _publish(task_id, {"type": WSEventType.PROGRESS, "step": "llm_analysis", "pct": 80, "message": "Generating AI analysis..."})
        repo_root = ctx_data.get("repo_root", ".")
        reviewers = ownership_analyzer.get_reviewer_recommendations(retrieved, repo_root)
        if reviewers:
            _publish(task_id, {"type": WSEventType.RECOMMENDATIONS, "reviewers": reviewers})
            
        messages = build_query_prompt(changed_symbol, change_summary, retrieved, graph_summary, cdl_delta)
        
        async def run_llm():
            from backend.websocket import publish_progress
            full_response = ""
            async for text_delta in call_llm_streaming(messages):
                full_response += text_delta
                await publish_progress(task_id, {"type": WSEventType.DELTA, "text": text_delta})
            return full_response
            
        full_response = _run_async(run_llm())
        validated = validate_response(full_response, retrieved)
        
        # Fix #9: Use WSEventType.COMPLETE instead of raw "analysis_complete"
        _publish(task_id, {
            "type": WSEventType.COMPLETE,
            "task_id": task_id,
            "result": validated.model_dump(),
            "pct": 100,
        })

        # Fix #10: Clean up context after completion
        from backend.core.context_store import delete_context
        _run_async(delete_context(request_id))

    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        # Fix #1: logger is now defined — no more NameError
        logger.error(f"Analysis failed: {err_msg}")
        # Fix #9: Use WSEventType.ERROR instead of raw "error"
        _publish(task_id, {"type": WSEventType.ERROR, "message": str(e) or "Error (see logs)", "traceback": err_msg})
