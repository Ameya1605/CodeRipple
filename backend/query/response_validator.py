import json
from typing import List, Dict, Any
from pydantic import BaseModel
from backend.indexer.schema import CodeChunk

class ValidatedResponse(BaseModel):
    risk_tier: str
    summary: str
    test_gap_suggestions: List[Dict[str, Any]]
    hallucinations_stripped: bool

def validate_response(full_text: str, retrieved_chunks: List[CodeChunk]) -> ValidatedResponse:
    test_gaps = []
    json_start = full_text.find('[')
    json_end = full_text.rfind(']') + 1
    
    if json_start != -1 and json_end > json_start:
        try:
            test_gaps = json.loads(full_text[json_start:json_end])
        except Exception:
            pass
            
    tier = "UNKNOWN"
    for t in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if t in full_text:
            tier = t
            break
            
    valid_ids = {c.chunk_id for c in retrieved_chunks}
    stripped = False
    
    clean_gaps = []
    for gap in test_gaps:
        if "chunk_id" in gap and gap["chunk_id"] not in valid_ids:
            stripped = True
            continue
        clean_gaps.append(gap)
        
    summary_text = full_text[:json_start].strip() if json_start != -1 else full_text.strip()
        
    return ValidatedResponse(
        risk_tier=tier,
        summary=summary_text,
        test_gap_suggestions=clean_gaps,
        hallucinations_stripped=stripped
    )
