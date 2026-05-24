import logging
from typing import Dict, Any, List, AsyncGenerator
from backend.indexer.schema import CodeChunk
from backend.retrieval.retriever import retrieve_dependents, build_call_graph_summary
from backend.query.prompt_builder import build_query_prompt
from backend.query.llm_client import call_llm_streaming
from backend.query.response_validator import validate_response

logger = logging.getLogger(__name__)

async def analyze_impact(changed_symbol: CodeChunk, change_summary: str) -> Dict[str, Any]:
    """
    High-level orchestration for dependency impact analysis.
    """
    logger.info(f"Analyzing impact for {changed_symbol.qualified_name}")
    
    # 1. Retrieve dependents (Vector + Graph + Contract)
    retrieved = await retrieve_dependents(changed_symbol)
    
    # 2. Build graph summary (Neo4j)
    graph_summary = await build_call_graph_summary(changed_symbol.qualified_name, changed_symbol.repo_id)
    
    # 3. Build Prompt
    messages = build_query_prompt(changed_symbol, change_summary, retrieved, graph_summary)
    
    # 4. Call LLM (Streaming)
    full_response = ""
    async for text_delta in call_llm_streaming(messages):
        full_response += text_delta
        
    # 5. Validate Response
    validation = validate_response(full_response, retrieved)
    
    return {
        "changed_symbol": changed_symbol.model_dump(),
        "retrieved_dependents": [r.model_dump() for r in retrieved],
        "graph_summary": graph_summary,
        "analysis": full_response,
        "validation": validation.model_dump()
    }
