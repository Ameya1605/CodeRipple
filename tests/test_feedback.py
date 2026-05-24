from backend.indexer.schema import CodeChunk
from backend.intelligence.feedback_loop import FeedbackLoopEngine
from backend.intelligence.risk_engine import RiskScoreEngine

def test_feedback_loop_bump():
    engine = FeedbackLoopEngine()
    
    chunk = CodeChunk(
        chunk_id="api:login",
        repo_id="api",
        file_path="login.py",
        symbol_type="func",
        symbol_name="login",
        qualified_name="login",
        start_line=1,
        end_line=10,
        signature="def login()",
        content="pass",
        language="python",
        risk_score_current=0.2, # Base low score
        break_count_90d=0,
        churn_score=0.1,
        test_coverage_pct=0.9,
        is_on_critical_path=False
    )
    
    # Calculate exact baseline score
    risk_calc = RiskScoreEngine()
    base_score = risk_calc.compute(chunk, fan_out=5)
    chunk.risk_score_current = base_score
    
    incident_data = {
        "id": "INC-1234",
        "suspect_chunk_ids": ["api:login"]
    }
    
    updated_chunks = engine.ingest_incident(incident_data, [chunk])
    updated_chunk = updated_chunks[0]
    
    assert updated_chunk.break_count_90d == 1
    assert len(updated_chunk.risk_score_history) == 1
    
    # Risk score should bump by at least 0.15
    assert updated_chunk.risk_score_current >= base_score + 0.15
