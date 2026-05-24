"""
Vector store — Fix #6: Uses typed embedding_vector. Fix #7: Typed CollectionNotFoundError.
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest
from backend.config import (
    QDRANT_URL, 
    COLLECTION_SYMBOLS, 
    COLLECTION_CONTRACTS, 
    COLLECTION_ANALYSES,
    EMBEDDING_DIM
)
from backend.indexer.schema import CodeChunk

logger = logging.getLogger(__name__)


class CollectionNotFoundError(RuntimeError):
    """Fix #7: Raised when a Qdrant collection doesn't exist (repo not yet indexed)."""
    pass


class VectorStore:
    def __init__(self, url: str = QDRANT_URL):
        self.client = AsyncQdrantClient(url=url, check_compatibility=False)
        
    async def init_collections(self):
        collections = [COLLECTION_SYMBOLS, COLLECTION_CONTRACTS, COLLECTION_ANALYSES]
        existing = await self.client.get_collections()
        existing_names = [c.name for c in existing.collections]
        
        for coll_name in collections:
            if coll_name not in existing_names:
                await self.client.create_collection(
                    collection_name=coll_name,
                    vectors_config=rest.VectorParams(
                        size=EMBEDDING_DIM,
                        distance=rest.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {coll_name}")
                
    async def upsert_chunks(self, chunks: List[CodeChunk], collection: str = COLLECTION_SYMBOLS):
        if not chunks:
            return
            
        points = []
        for chunk in chunks:
            # Fix #6: Use typed embedding_vector field instead of dynamic _embedding_vector
            if chunk.embedding_vector is None:
                continue
                
            # Serialize payload natively handling complex nested lists
            payload = chunk.model_dump(exclude={"embedding_vector"})
            points.append(
                rest.PointStruct(
                    id=chunk.chunk_id,
                    vector=chunk.embedding_vector,
                    payload=payload
                )
            )
            
        if points:
            await self.client.upsert(
                collection_name=collection,
                points=points
            )
            logger.info(f"Upserted {len(points)} points to {collection}")

    async def search(
        self, 
        collection: str, 
        vector: List[float], 
        limit: int = 10, 
        score_threshold: float = 0.60,
        filters: Optional[List[rest.FieldCondition]] = None
    ) -> List[Dict[str, Any]]:
        
        query_filter = None
        if filters:
            query_filter = rest.Filter(must=filters)
            
        try:
            results = await self.client.query_points(
                collection_name=collection,
                query=vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True
            )
            return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results.points]
        except Exception as e:
            error_str = str(e).lower()
            if "404" in error_str or "not found" in error_str or "doesn't exist" in error_str:
                # Fix #7: Raise typed exception instead of silently returning []
                logger.warning(
                    f"Collection '{collection}' not found in Qdrant. "
                    "The repository has not been indexed yet. "
                    "Run: dia index --repo /path/to/repo"
                )
                raise CollectionNotFoundError(
                    f"Collection '{collection}' not found. Index the repository first."
                )
            logger.error(f"Qdrant search failed: {e}")
            raise

vector_store = VectorStore()
