"""
Embedder — Fix #6: Uses typed embedding_vector field. Fix #11: Fully async.
"""
import logging
from typing import List
from backend.indexer.schema import CodeChunk
from backend.config import EMBEDDING_PROVIDER

logger = logging.getLogger(__name__)

from backend.ai.factory import embedding_provider

def build_embedding_text(chunk: CodeChunk) -> str:
    parts = [
        f"Language: {chunk.language}",
        f"{chunk.symbol_type} {chunk.qualified_name}",
        f"Signature: {chunk.signature}",
    ]
    if chunk.docstring:
        parts.append(f"Purpose: {chunk.docstring[:400]}")
    if chunk.calls:
        parts.append("Calls: " + ", ".join(chunk.calls[:10]))
    if chunk.called_by:
        parts.append("Called by: " + ", ".join(chunk.called_by[:10]))
    
    parts.append(f"Service: {chunk.service} | Owner: {chunk.team_owner}")
    parts.append(f"API surface: {chunk.api_surface}")
    
    if chunk.content:
        # Include first 1000 chars of content for implementation-aware retrieval
        parts.append(f"Implementation: {chunk.content[:1000]}")

    if chunk.is_on_critical_path:
        parts.append("CRITICAL PATH: true")
    
    if chunk.risk_score_history:
        r = chunk.risk_score_history[-1]
        parts.append(f"Risk tier: {r.tier} | Score: {r.score:.2f}")
        
    if chunk.break_count_90d > 0:
        parts.append(f"Breaks in 90d: {chunk.break_count_90d}")
        
    if chunk.contract_type:
        parts.append(f"Contract: {chunk.contract_type}")
        
    return " | ".join(parts)

async def embed_chunks(chunks: List[CodeChunk], batch_size: int = 100) -> List[CodeChunk]:
    """
    Fix #6:  Sets chunk.embedding_vector (typed field) instead of chunk._embedding_vector (dynamic).
    Fix #11: Only calls async methods — no sync I/O in this async function.
    """
    if not chunks:
        return chunks

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [build_embedding_text(c) for c in batch]
        for idx, c in enumerate(batch): c.embedding_text = texts[idx]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                responses = await embedding_provider.embed_batch(texts)
                success_count = 0
                for j, resp in enumerate(responses):
                    if resp.vector and any(v != 0.0 for v in resp.vector):
                        # Fix #6: Use typed field instead of dynamic attribute
                        batch[j].embedding_vector = resp.vector
                        success_count += 1
                    else:
                        batch[j].embedding_vector = None
                        logger.warning(f"Zero/empty vector for chunk: {batch[j].qualified_name}")
                
                logger.info(f"Embedded {success_count}/{len(batch)} chunks in batch {i // batch_size + 1}")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to embed batch after {max_retries} attempts: {e}")
                else:
                    import asyncio
                    sleep_time = 2 ** attempt
                    logger.warning(f"Embedding failed, retrying in {sleep_time}s: {e}")
                    await asyncio.sleep(sleep_time)
                    
    return chunks
