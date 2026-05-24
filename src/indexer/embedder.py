import time
import logging
import os
from typing import List, Tuple
from src.indexer.schema import CodeChunk
from src.config import EMBEDDING_MODEL, GEMINI_API_KEY, LLM_PROVIDER
import google.generativeai as genai

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

try:
    from openai import OpenAI
    openai_client = OpenAI() if os.environ.get("OPENAI_API_KEY") else None
except ImportError:
    openai_client = None

def build_embedding_text(chunk: CodeChunk) -> str:
    parts = []
    parts.append(f"Type: {chunk.symbol_type}")
    parts.append(f"Name: {chunk.qualified_name}")
    parts.append(f"Signature: {chunk.signature}")
    
    if chunk.docstring:
        parts.append(f"Docstring: {chunk.docstring[:400]}")
        
    if chunk.calls:
        parts.append(f"Calls: {', '.join(chunk.calls[:10])}")
        
    if chunk.called_by:
        parts.append(f"Called By: {', '.join(chunk.called_by[:10])}")
        
    parts.append(f"Service: {chunk.service}")
    parts.append(f"Team: {chunk.team_owner}")
    
    result = " | ".join(parts)
    chunk.embedding_text = result
    chunk.embedding_model_version = EMBEDDING_MODEL
    return result

def embed_chunks(chunks: List[CodeChunk]) -> List[Tuple[CodeChunk, List[float]]]:
    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        return _embed_with_gemini(chunks)
        
    if not openai_client:
        logger.error("No LLM provider configured for embeddings.")
        raise Exception("LLM provider not configured.")

    # Ensure text is built
    for chunk in chunks:
        if not chunk.embedding_text:
            build_embedding_text(chunk)
            
    batch_size = 100
    results = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.embedding_text for c in batch]
        
        retries = 3
        wait_time = 1
        
        for attempt in range(retries):
            try:
                response = openai_client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
                for j, data in enumerate(response.data):
                    results.append((batch[j], data.embedding))
                break
            except Exception as e:
                logger.warning(f"Embedding batch failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(wait_time)
                wait_time *= 2
                
    return results

def _embed_with_gemini(chunks: List[CodeChunk]) -> List[Tuple[CodeChunk, List[float]]]:
    for chunk in chunks:
        if not chunk.embedding_text:
            build_embedding_text(chunk)
            
    results = []
    batch_size = 50 # Gemini batch limit
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.embedding_text for c in batch]
        
        # Add delay between batches to stay under Free Tier RPS limits
        if i > 0:
            time.sleep(5)
            
        retries = 10
        wait_time = 10
        
        for attempt in range(retries):
            try:
                res = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=texts,
                    task_type="retrieval_document"
                )
                for j, emb in enumerate(res['embedding']):
                    results.append((batch[j], emb))
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt == retries - 1:
                        logger.error(f"Gemini rate limit exceeded after {retries} attempts.")
                        raise e
                    logger.warning(f"Gemini rate limit hit, retrying in {wait_time}s... (Attempt {attempt+1}/{retries})")
                    time.sleep(wait_time)
                    wait_time = min(wait_time * 2, 60) # Cap at 60s
                else:
                    logger.error(f"Gemini embedding failed: {e}")
                    raise e
            
    return results
