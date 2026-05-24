from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from backend.indexer.schema import CodeChunk
from backend.intelligence.feedback_loop import FeedbackLoopEngine

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

class Incident(BaseModel):
    id: str
    suspect_chunk_ids: List[str]
    resolved_at: str = None

# Mock global chunks list for Phase 9 gate
MOCK_DB_CHUNKS = [
    CodeChunk(
        chunk_id="core:main",
        repo_id="core",
        file_path="main.py",
        symbol_type="func",
        symbol_name="main",
        qualified_name="main",
        start_line=1,
        end_line=10,
        signature="def main()",
        content="pass",
        language="python",
        risk_score_current=0.2,
        break_count_90d=0
    )
]

class AnalysisFeedback(BaseModel):
    request_id: str
    symbol_id: str
    is_correct: bool
    comments: str = None

@router.post("/analysis")
async def submit_analysis_feedback(feedback: AnalysisFeedback):
    """
    Stores human feedback on a specific AI analysis.
    """
    engine = FeedbackLoopEngine()
    engine.record_analysis_feedback(
        request_id=feedback.request_id,
        symbol_id=feedback.symbol_id,
        is_correct=feedback.is_correct,
        comments=feedback.comments
    )
    return {"status": "recorded", "request_id": feedback.request_id}

@router.post("/incident")
async def report_incident(incident: Incident):
    engine = FeedbackLoopEngine()
    updated_chunks = engine.ingest_incident(incident.model_dump(), MOCK_DB_CHUNKS)
    return {"processed": True, "updated_chunks": [c.chunk_id for c in updated_chunks if c.break_count_90d > 0]}
