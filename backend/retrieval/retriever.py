"""
Retriever module.
Fix #6: Uses typed embedding_vector.
Fix #7: Handles CollectionNotFoundError.
Fix #8: Handles Neo4j graph expansion failure gracefully.
"""
import logging
from typing import List, Dict, Any, Optional
from backend.indexer.schema import CodeChunk
from backend.indexer.vector_store import vector_store, CollectionNotFoundError
from backend.graph.neo4j_client import neo4j_client
from backend.graph.queries import CRITICAL_CALLERS, CIRCULAR_DEPS, get_blast_radius
from backend.indexer.embedder import build_embedding_text, embed_chunks
from backend.config import (
    COLLECTION_SYMBOLS, COLLECTION_CONTRACTS, 
    MAX_RETRIEVED, PHASE_A_CANDIDATES, PHASE_A_MIN_SCORE
)

logger = logging.getLogger(__name__)

async def build_call_graph_summary(qname: str, repo_id: str) -> Dict[str, Any]:
    summary = {"total_callers": 0, "critical_callers": 0, "cycles": []}
    try:
        async with neo4j_client.session() as session:
            # Basic stats
            res = await session.run(
                "MATCH (caller:Symbol)-[:CALLS]->(s:Symbol {qualified_name: $qname, repo_id: $repo_id}) RETURN count(caller) as c",
                qname=qname, repo_id=repo_id
            )
            records = await res.data()
            if records: summary["total_callers"] = records[0]["c"]
            
            # Critical callers
            res = await session.run(CRITICAL_CALLERS, qname=qname, repo_id=repo_id)
            callers = [record["caller"]["qualified_name"] for record in await res.data()]
            summary["critical_callers"] = len(callers)
            
            # Cycles
            res = await session.run(CIRCULAR_DEPS, qname=qname)
            cycles = await res.data()
            summary["cycles"] = [c["cycle"] for c in cycles]
            
            # Extract nodes and edges for UI
            records = await get_blast_radius(session, qname, max_depth=2)
            nodes = {qname: {"id": qname, "type": "custom", "data": {"label": qname.split('.')[-1], "tier": "CRITICAL", "fanOut": 0}}}
            for record in records:
                node_name = record["name"]
                depth = record["depth"]
                if depth is None: continue
                if not node_name or node_name == qname: continue
                
                tier = "HIGH" if depth == 1 else "MEDIUM" if depth == 2 else "LOW"
                nodes[node_name] = {
                    "id": node_name,
                    "type": "custom",
                    "data": {"label": node_name.split('.')[-1], "tier": tier, "fanOut": 0}
                }
                
            qnames = list(nodes.keys())
            edges = []
            if len(qnames) > 1:
                edge_res = await session.run(
                    """
                    MATCH (n:Symbol)-[r:CALLS]->(m:Symbol)
                    WHERE n.qualified_name IN $qnames AND m.qualified_name IN $qnames
                    RETURN n.qualified_name as source, m.qualified_name as target
                    """,
                    qnames=qnames
                )
                for record in await edge_res.data():
                    edges.append({"id": f"e_{record['source']}_{record['target']}", "source": record['source'], "target": record['target']})
                    if record['source'] in nodes:
                        nodes[record['source']]["data"]["fanOut"] += 1
                        
            # Basic layout
            for i, (nid, ndata) in enumerate(nodes.items()):
                ndata["position"] = {"x": 250 + (i % 3) * 150 - 150, "y": 50 + (i // 3) * 100}
                
            summary["nodes"] = list(nodes.values())
            summary["edges"] = edges
    except Exception as e:
        logger.error(f"Failed to build call graph summary: {e}")
    return summary

async def retrieve_dependents(changed_chunk: CodeChunk, cross_repo: bool = False) -> List[CodeChunk]:
    results_map = {} # qname -> dict of chunk and scores
    
    # Phase A — Vector Seed
    changed_chunk.embedding_text = build_embedding_text(changed_chunk)
    await embed_chunks([changed_chunk])
    
    # Fix #6: Use typed field instead of hasattr
    if changed_chunk.embedding_vector is not None:
        from qdrant_client.http import models as rest
        filters = None
        if not cross_repo:
            filters = [rest.FieldCondition(key="repo_id", match=rest.MatchValue(value=changed_chunk.repo_id))]
            
        try:
            vector_results = await vector_store.search(
                COLLECTION_SYMBOLS, 
                changed_chunk.embedding_vector,
                limit=PHASE_A_CANDIDATES,
                score_threshold=PHASE_A_MIN_SCORE,
                filters=filters
            )
            
            for r in vector_results:
                payload = r["payload"]
                qname = payload["qualified_name"]
                results_map[qname] = {
                    "chunk": CodeChunk(**payload),
                    "vector_score": r["score"],
                    "depth": 99 # unknown depth initially
                }
        except CollectionNotFoundError:
            # Fix #7: Repository not indexed
            logger.warning("Repository not indexed — skipping vector search phase")
            # We don't have task_id here to publish, but it won't crash
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            
    # Phase B — Neo4j Graph Expansion
    try:
        async with neo4j_client.session() as session:
            records = await get_blast_radius(session, changed_chunk.qualified_name, max_depth=3)
            for record in records:
                qname = record["name"]
                depth = record["depth"]
                if not qname: continue
                
                if qname in results_map:
                    results_map[qname]["depth"] = min(results_map[qname]["depth"], depth)
                else:
                    # We only get partial data from native cypher (no full node properties)
                    # We'll create a minimal CodeChunk
                    results_map[qname] = {
                        "chunk": CodeChunk(
                            chunk_id=f"graph_{qname}",
                            repo_id=changed_chunk.repo_id,
                            file_path=record.get("file", ""),
                            symbol_type="unknown",
                            symbol_name=qname.split('.')[-1],
                            qualified_name=qname,
                            start_line=1,
                            end_line=1,
                            signature="",
                            content="[Graph only node]",
                            language="unknown"
                        ),
                        "vector_score": 0.0,
                        "depth": depth
                    }
                    
            # Critical callers forced to depth 1
            res = await session.run(CRITICAL_CALLERS, qname=changed_chunk.qualified_name, repo_id=changed_chunk.repo_id)
            for record in await res.data():
                caller = record["caller"]
                qname = caller.get("qualified_name")
                if not qname: continue
                
                if qname in results_map:
                    results_map[qname]["depth"] = 1
                else:
                    results_map[qname] = {
                        "chunk": CodeChunk(**caller),
                        "vector_score": 0.0,
                        "depth": 1
                    }
    except Exception as e:
        # Fix #8: Warn but don't crash
        logger.error(f"Neo4j graph expansion failed: {e}")

    # Phase C — Contract Expansion (cross-repo)
    if changed_chunk.contract_type and cross_repo and changed_chunk.embedding_vector is not None:
        try:
            contract_results = await vector_store.search(
                COLLECTION_CONTRACTS, 
                changed_chunk.embedding_vector,
                limit=5
            )
            for r in contract_results:
                payload = r["payload"]
                qname = payload["qualified_name"]
                if qname not in results_map:
                    results_map[qname] = {
                        "chunk": CodeChunk(**payload),
                        "vector_score": 0.0,
                        "depth": 4 # Cross service penalty depth
                    }
        except Exception as e:
            logger.error(f"Contract expansion failed: {e}")

    # Final ranking using Phase 4 Reranker
    from backend.retrieval.reranker import reranker
    candidates = list(results_map.values())
    return reranker.rerank(changed_chunk, candidates, limit=MAX_RETRIEVED)

async def get_symbol_by_qname(qname: str, repo_id: str) -> Optional[CodeChunk]:
    """
    Retrieves the latest indexed version of a symbol from Neo4j.
    """
    try:
        async with neo4j_client.session() as session:
            res = await session.run(
                "MATCH (s:Symbol {qualified_name: $qname, repo_id: $repo_id}) RETURN s LIMIT 1",
                qname=qname, repo_id=repo_id
            )
            record = await res.single()
            if record:
                return CodeChunk(**record["s"])
    except Exception as e:
        logger.error(f"Failed to fetch symbol {qname}: {e}")
    return None
