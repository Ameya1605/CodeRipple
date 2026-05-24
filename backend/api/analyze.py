"""
Analyze endpoint — Fix #10: Uses context_store instead of fallback_store.
"""
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.auth.dependencies import require_role
from backend.auth.models import User
from backend.indexer.schema import CodeChunk
from backend.jobs.tasks import run_analysis
from backend.config import effective_broker_url
from backend.core.context_store import save_context

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"])

class AnalyzeRequest(BaseModel):
    chunk: CodeChunk
    change_summary: str

@router.post("/symbol", status_code=202)
async def analyze_symbol_request(req: AnalyzeRequest, user: User = Depends(require_role("developer"))):
    request_id = str(uuid.uuid4())
    
    # Fix #10: Save context via Redis
    ctx = {
        "changed_symbol": req.chunk.model_dump(),
        "change_summary": req.change_summary,
        "repo_id": req.chunk.repo_id,
        "target": req.chunk.qualified_name,
        "request_id": request_id,
        "submitted_at": datetime.utcnow().isoformat(),
    }
    
    saved = await save_context(request_id, ctx)
    if not saved:
        raise HTTPException(status_code=503, detail="Context store unavailable (Redis is down)")

    try:
        task = run_analysis.apply_async(
            kwargs={
                "request_id": request_id,
                "repo_id": req.chunk.repo_id,
                "target": req.chunk.qualified_name,
            },
            task_id=f"analysis-{request_id}",
        )
        logger.info(f"Task dispatched: {task.id} to broker {effective_broker_url}")
        return {"request_id": request_id, "task_id": task.id, "status": "queued"}
    except Exception as e:
        logger.error(f"Task dispatch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Task broker unavailable: {str(e)}")

@router.post("/diff", status_code=202)
async def analyze_diff_request(req: AnalyzeRequest, user: User = Depends(require_role("developer"))):
    return await analyze_symbol_request(req, user)

@router.post("/generate-tests")
async def generate_tests(chunk: CodeChunk, user: User = Depends(require_role("developer"))):
    from backend.intelligence.test_gen import test_generator
    skeleton = await test_generator.generate_skeleton(chunk)
    return {"skeleton": skeleton}

@router.get("/history/{qname}")
async def get_history(qname: str):
    return [] # Stubbed for Phase 9
