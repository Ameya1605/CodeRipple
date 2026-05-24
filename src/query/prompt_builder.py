from typing import List, Dict
from src.indexer.schema import CodeChunk
from src.retrieval.retriever import RetrievedDependent

def build_query_prompt(
    system_prompt: str, 
    changed_chunk: CodeChunk, 
    change_summary: str, 
    retrieved: List[RetrievedDependent], 
    call_graph_summary: Dict
) -> List[Dict]:
    
    retrieved_text = ""
    for dep in retrieved:
        retrieved_text += f"[{dep.relationship_type.upper()}] {dep.chunk.qualified_name} (Depth: {dep.depth})\n"
        if dep.relevant_snippet:
            retrieved_text += f"Snippet:\n{dep.relevant_snippet}\n"
            
    call_graph_text = "\n".join(f"{k}: {v}" for k, v in call_graph_summary.items())
    
    user_message = f"""Here is the change description:
{change_summary}

<CHANGED_SYMBOL>
Name: {changed_chunk.qualified_name}
Type: {changed_chunk.symbol_type}
Signature: {changed_chunk.signature}
Docstring: {changed_chunk.docstring}
</CHANGED_SYMBOL>

<RETRIEVED_DEPENDENTS>
{retrieved_text}
</RETRIEVED_DEPENDENTS>

<CALL_GRAPH_SUMMARY>
{call_graph_text}
</CALL_GRAPH_SUMMARY>
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
