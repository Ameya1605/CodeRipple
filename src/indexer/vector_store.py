from typing import List, Tuple, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
from src.indexer.schema import CodeChunk
from src.config import QDRANT_URL, COLLECTION_NAME, EMBEDDING_DIM, EMBEDDING_MODEL, GEMINI_API_KEY, LLM_PROVIDER
import google.generativeai as genai
import os

if QDRANT_URL.startswith("http"):
    qdrant = QdrantClient(url=QDRANT_URL)
else:
    qdrant = QdrantClient(path=QDRANT_URL)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

try:
    from openai import OpenAI
    openai_client = OpenAI() if os.environ.get("OPENAI_API_KEY") else None
except ImportError:
    openai_client = None

def init_collection():
    collections = qdrant.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )

def _chunk_id_to_int(chunk_id: str) -> int:
    # Handle both hex and non-hex IDs
    try:
        return int(chunk_id[:8], 16)
    except ValueError:
        # Simple hash if not hex
        import hashlib
        return int(hashlib.md5(chunk_id.encode()).hexdigest()[:8], 16)

def upsert_chunks(chunks_with_vectors: List[Tuple[CodeChunk, List[float]]]):
    points = []
    for chunk, vector in chunks_with_vectors:
        point_id = _chunk_id_to_int(chunk.chunk_id)
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=chunk.model_dump()
            )
        )
    
    if points:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

def search(query_text: str, top_k: int = 50, filters: Dict[str, Any] = None) -> List[Any]:
    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        res = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query_text,
            task_type="retrieval_query"
        )
        query_vector = res['embedding']
    elif openai_client:
        response = openai_client.embeddings.create(input=[query_text], model=EMBEDDING_MODEL)
        query_vector = response.data[0].embedding
    else:
        raise Exception("No embedding provider configured.")
    
    qdrant_filter = None
    if filters:
        conditions = []
        for k, v in filters.items():
            conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
        qdrant_filter = Filter(must=conditions)
        
    return qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=qdrant_filter,
        limit=top_k
    )
