import logging
import datetime
import json
import os
from typing import List, Dict, Any
from backend.indexer.schema import CodeChunk, RiskEvent
from backend.intelligence.risk_engine import RiskScoreEngine

logger = logging.getLogger(__name__)

FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedback_data")

class FeedbackLoopEngine:
    def __init__(self):
        self.risk_engine = RiskScoreEngine()
        if not os.path.exists(FEEDBACK_DIR):
            os.makedirs(FEEDBACK_DIR, exist_ok=True)

    def ingest_incident(self, incident_data: Dict[str, Any], chunks: List[CodeChunk]) -> List[CodeChunk]:
        """
        Receives incident data (e.g. from PagerDuty), extracts the suspected chunk IDs,
        and updates their historical risk metrics.
        """
        incident_id = incident_data.get("id", "unknown")
        suspect_chunk_ids = incident_data.get("suspect_chunk_ids", [])
        resolved_at = incident_data.get("resolved_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
        
        logger.info(f"Ingesting incident {incident_id} affecting {len(suspect_chunk_ids)} chunks")
        
        for chunk in chunks:
            if chunk.chunk_id in suspect_chunk_ids:
                # 1. Increment 90-day break count
                chunk.break_count_90d += 1
                
                # 2. Add to risk history
                event = RiskEvent(
                    timestamp=resolved_at,
                    score=chunk.risk_score_current, # previous score
                    tier=self.risk_engine.to_tier(chunk.risk_score_current),
                    reason=f"Incident {incident_id}"
                )
                if chunk.risk_score_history is None:
                    chunk.risk_score_history = []
                chunk.risk_score_history.append(event)
                
                # 3. Auto-adjust chunk-specific weight modifier via the RiskEngine
                new_score = self.risk_engine.compute(chunk, 5) # Default fan out for recompute
                
                logger.info(f"Chunk {chunk.chunk_id} risk score bumped from {chunk.risk_score_current} to {new_score}")
                chunk.risk_score_current = new_score
                
        return chunks

    def record_analysis_feedback(self, request_id: str, symbol_id: str, is_correct: bool, comments: str = None):
        """
        Persists human feedback on an AI analysis.
        """
        feedback_entry = {
            "request_id": request_id,
            "symbol_id": symbol_id,
            "is_correct": is_correct,
            "comments": comments,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        filename = f"feedback_{request_id}_{symbol_id}.json"
        filepath = os.path.join(FEEDBACK_DIR, filename)
        
        with open(filepath, "w") as f:
            json.dump(feedback_entry, f, indent=2)
            
        logger.info(f"Recorded feedback for request {request_id}, symbol {symbol_id}: {is_correct}")

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """
        Retrieves all stored feedback entries.
        """
        if not os.path.exists(FEEDBACK_DIR):
            return []
            
        feedback_list = []
        for filename in os.listdir(FEEDBACK_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(FEEDBACK_DIR, filename), "r") as f:
                    feedback_list.append(json.load(f))
        return feedback_list

    def optimize_reranker_weights(self) -> Dict[str, float]:
        """
        Analyzes feedback to suggest improvements for RERANK_VECTOR_W, RERANK_GRAPH_W, and RERANK_RISK_W.
        If many false positives are linked to high vector similarity but low graph connectivity,
        it suggests increasing RERANK_GRAPH_W.
        """
        feedbacks = self.get_all_feedback()
        if not feedbacks:
            return {}
            
        total = len(feedbacks)
        false_positives = [f for f in feedbacks if not f.get("is_correct")]
        fp_count = len(false_positives)
        
        if fp_count == 0:
            return {"status": "current weights optimal"}
            
        # Simplified optimization logic: 
        # If FP rate is high (> 20%), slightly shift weight from Vector to Graph/Risk
        fp_rate = fp_count / total
        
        suggested_weights = {
            "RERANK_VECTOR_W": 0.60,
            "RERANK_GRAPH_W": 0.25,
            "RERANK_RISK_W": 0.15
        }
        
        if fp_rate > 0.2:
            shift = min(fp_rate * 0.1, 0.15)
            suggested_weights["RERANK_VECTOR_W"] -= shift
            suggested_weights["RERANK_GRAPH_W"] += (shift / 2)
            suggested_weights["RERANK_RISK_W"] += (shift / 2)
            
        logger.info(f"Suggested weight optimization (FP rate {fp_rate:.2f}): {suggested_weights}")
        return suggested_weights

    def get_corrected_examples(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves a few recent feedback entries that were marked as "False Positives"
        to use as negative examples in few-shot prompting.
        """
        feedbacks = self.get_all_feedback()
        # Sort by timestamp descending
        feedbacks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # We specifically want examples where the AI was WRONG (is_correct=False)
        negative_examples = [f for f in feedbacks if not f.get("is_correct")]
        
        return negative_examples[:limit]
