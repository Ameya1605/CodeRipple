from typing import List, Dict, Set
from pydantic import BaseModel
import networkx as nx
from src.indexer.schema import CodeChunk
from src.indexer.vector_store import search
from src.indexer.vector_store_helpers import get_chunk_by_qname
from src.config import PHASE1_MIN_SCORE, RERANK_VECTOR_WEIGHT, RERANK_GRAPH_WEIGHT

class RetrievedDependent(BaseModel):
    chunk: CodeChunk
    vector_score: float
    depth: int
    relationship_type: str
    final_score: float = 0.0
    call_sites: List[int] = []
    relevant_snippet: str = ""

def _find_call_sites(file_path: str, symbol_name: str) -> tuple[List[int], str]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        sites = []
        snippet = ""
        for i, line in enumerate(lines):
            # Naive token check
            if symbol_name in line:
                sites.append(i + 1)
                if not snippet:
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    snippet = "".join(lines[start:end])
        return sites, snippet
    except Exception:
        return [], ""

def retrieve_dependents(changed_chunk: CodeChunk, graph: nx.DiGraph, top_k: int = 20) -> List[RetrievedDependent]:
    working_set: Dict[str, RetrievedDependent] = {}
    
    # Phase 1 - Seed Retrieval
    search_results = search(
        query_text=changed_chunk.embedding_text,
        top_k=50,
        filters={"language": changed_chunk.language}
    )
    
    for point in search_results:
        if point.score < PHASE1_MIN_SCORE:
            continue
            
        chunk = CodeChunk(**point.payload)
        qname = chunk.qualified_name
        
        rel_type = "similar"
        if qname in changed_chunk.called_by:
            rel_type = "caller"
        elif qname in changed_chunk.test_coverage:
            rel_type = "test"
        elif any(imp.endswith(changed_chunk.qualified_name.split('.')[-1]) for imp in chunk.imports):
            rel_type = "importer"
        elif chunk.is_exported:
            rel_type = "re-exporter"
            
        working_set[qname] = RetrievedDependent(
            chunk=chunk,
            vector_score=point.score,
            depth=1,
            relationship_type=rel_type
        )
        
    # Phase 2 - Graph Expansion
    current_qnames = list(working_set.keys())
    for qname in current_qnames:
        if qname not in graph:
            continue
            
        # depth 2
        for pred2 in graph.predecessors(qname):
            if pred2 not in working_set:
                pred2_chunk = get_chunk_by_qname(pred2)
                if pred2_chunk:
                    working_set[pred2] = RetrievedDependent(
                        chunk=pred2_chunk,
                        vector_score=0.0,
                        depth=2,
                        relationship_type="indirect_caller"
                    )
            
            # depth 3
            if pred2 in graph:
                for pred3 in graph.predecessors(pred2):
                    if pred3 not in working_set:
                        pred3_chunk = get_chunk_by_qname(pred3)
                        if pred3_chunk:
                            working_set[pred3] = RetrievedDependent(
                                chunk=pred3_chunk,
                                vector_score=0.0,
                                depth=3,
                                relationship_type="indirect_caller"
                            )

    # Re-ranking and Snippets
    results = []
    for qname, dep in working_set.items():
        dep.final_score = (dep.vector_score * RERANK_VECTOR_WEIGHT) + ((1.0 / dep.depth) * RERANK_GRAPH_WEIGHT)
        
        sites, snippet = _find_call_sites(dep.chunk.file_path, changed_chunk.symbol_name)
        dep.call_sites = sites
        dep.relevant_snippet = snippet
        
        results.append(dep)
        
    results.sort(key=lambda x: x.final_score, reverse=True)
    return results[:top_k]

def build_call_graph_summary(changed_chunk: CodeChunk, graph: nx.DiGraph, retrieved: List[RetrievedDependent]) -> Dict:
    direct_callers = 0
    indirect_callers = 0
    
    qname = changed_chunk.qualified_name
    if qname in graph:
        direct_callers = len(list(graph.predecessors(qname)))
        
        # bfs for indirect (depth 2 and 3)
        visited = set()
        queue = [(qname, 0)]
        while queue:
            curr, depth = queue.pop(0)
            if depth > 0 and curr not in visited:
                visited.add(curr)
                if depth > 1:
                    indirect_callers += 1
            if depth < 3 and curr in graph:
                for pred in graph.predecessors(curr):
                    if pred not in visited:
                        queue.append((pred, depth + 1))
                        
    test_count = sum(1 for d in retrieved if d.relationship_type == "test")
    services = list(set(d.chunk.service for d in retrieved if d.chunk.service))
    
    circular = "no"
    if qname in graph:
        try:
            cycle = nx.find_cycle(graph, qname)
            circular = "yes"
        except nx.NetworkXNoCycle:
            pass
            
    return {
        "direct_callers": direct_callers,
        "indirect_callers": indirect_callers,
        "test_count": test_count,
        "services": services,
        "circular": circular
    }
