import logging
from typing import List, Dict, Any
from backend.indexer.schema import CodeChunk
from backend.config import RERANK_VECTOR_W, RERANK_GRAPH_W, RERANK_RISK_W

logger = logging.getLogger(__name__)

class Reranker:
    """
    Reranks retrieved dependents based on a multi-dimensional score.
    """
    def rerank(
        self, 
        changed_chunk: CodeChunk, 
        candidates: List[Dict[str, Any]], 
        limit: int = 15
    ) -> List[CodeChunk]:
        """
        candidates: list of dicts with {"chunk": CodeChunk, "vector_score": float, "depth": int}
        """
        scored_chunks = []
        
        for item in candidates:
            chunk = item["chunk"]
            v_score = item.get("vector_score", 0.0)
            depth = item.get("depth", 99)
            
            # 1. Graph Score: closer is better. 1-hop = 1.0, 2-hop = 0.5, 3-hop = 0.33
            graph_score = 1.0 / depth if depth > 0 else 0.0
            
            # 2. Risk Score: symbols on critical path or with high current risk are prioritized
            risk_score = chunk.risk_score_current
            if chunk.is_on_critical_path:
                risk_score = max(risk_score, 0.8)
            
            # 3. Final weighted calculation
            final_score = (v_score * RERANK_VECTOR_W) + \
                          (graph_score * RERANK_GRAPH_W) + \
                          (risk_score * RERANK_RISK_W)
            
            scored_chunks.append((final_score, chunk))
            
        # Sort by final score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        return [chunk for score, chunk in scored_chunks[:limit]]

reranker = Reranker()
