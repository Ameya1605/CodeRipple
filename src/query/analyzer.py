import networkx as nx
from typing import Dict, Any
from src.indexer.vector_store_helpers import get_chunk_by_qname
from src.retrieval.retriever import retrieve_dependents, build_call_graph_summary
from src.query.system_prompt import SYSTEM_PROMPT
from src.query.prompt_builder import build_query_prompt
from src.query.llm_client import call_llm
from src.query.response_validator import validate_response

def analyze_change(qualified_name: str, change_summary: str, repo_root: str, graph: nx.DiGraph) -> Dict[str, Any]:
    chunk = get_chunk_by_qname(qualified_name)
    if not chunk:
        raise ValueError(f"Chunk not found for: {qualified_name}")
        
    retrieved = retrieve_dependents(chunk, graph)
    summary = build_call_graph_summary(chunk, graph, retrieved)
    
    messages = build_query_prompt(SYSTEM_PROMPT, chunk, change_summary, retrieved, summary)
    
    response_text = call_llm(messages)
    validation = validate_response(response_text, retrieved)
    
    return {
        "chunk": chunk.model_dump(),
        "retrieved_dependents": [d.model_dump() for d in retrieved],
        "call_graph_summary": summary,
        "raw_response": response_text,
        "validation": validation
    }
