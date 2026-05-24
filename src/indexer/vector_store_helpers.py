from typing import List, Dict, Any, Optional
from qdrant_client.models import Filter, FieldCondition, MatchValue
from src.indexer.schema import CodeChunk
from src.indexer.vector_store import qdrant, COLLECTION_NAME, _chunk_id_to_int

def get_chunk_by_id(chunk_id: str) -> Optional[CodeChunk]:
    point_id = _chunk_id_to_int(chunk_id)
    response = qdrant.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[point_id]
    )
    if response:
        return CodeChunk(**response[0].payload)
    return None

def get_chunk_by_qname(qualified_name: str) -> Optional[CodeChunk]:
    response = qdrant.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(must=[FieldCondition(key="qualified_name", match=MatchValue(value=qualified_name))]),
        limit=1
    )
    if response and response[0]:
        return CodeChunk(**response[0][0].payload)
    return None
