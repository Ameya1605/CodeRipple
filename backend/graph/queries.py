import logging

logger = logging.getLogger(__name__)

CRITICAL_CALLERS = """
MATCH (caller:Symbol)-[:CALLS]->(s:Symbol {qualified_name: $qname, repo_id: $repo_id})
WHERE caller.is_on_critical_path = true
RETURN caller
"""

CIRCULAR_DEPS = """
MATCH path = (s:Symbol {qualified_name: $qname})-[:CALLS*1..3]->(s)
RETURN [n in nodes(path) | n.qualified_name] as cycle
"""

# Fix #13: APOC-based and native fallback queries for blast radius
BLAST_RADIUS_APOC = """
CALL apoc.path.subgraphNodes(start, {
    relationshipFilter: "CALLS>|IMPORTS>|EXTENDS>|IMPLEMENTS>",
    maxLevel: $max_depth,
    bfs: true
}) YIELD node
RETURN node.qualified_name AS name, node.file_path AS file, labels(node) AS types,
       length(shortestPath((start)-[:CALLS*..10]->(node))) as depth
"""

BLAST_RADIUS_NATIVE = """
MATCH path = (start:Symbol {qualified_name: $qname})-[r:CALLS|IMPORTS|EXTENDS|IMPLEMENTS*1..4]->(dep:Symbol)
WHERE length(path) <= $max_depth
RETURN DISTINCT
    dep.qualified_name AS name,
    dep.file_path     AS file,
    labels(dep)       AS types,
    length(path)      AS depth
ORDER BY depth ASC
LIMIT 500
"""

async def verify_apoc_available(session) -> bool:
    """Returns True if APOC is loaded and the subgraphNodes procedure is available."""
    try:
        result = await session.run(
            "CALL dbms.procedures() YIELD name WHERE name = 'apoc.path.subgraphNodes' RETURN name"
        )
        records = await result.data()
        return len(records) > 0
    except Exception:
        return False

async def get_blast_radius(session, start_name: str, max_depth: int = 4) -> list[dict]:
    """Tries APOC first, falls back to native Cypher traversal if APOC unavailable."""
    apoc_ok = await verify_apoc_available(session)
    
    if apoc_ok:
        # Find start node first for apoc
        res = await session.run("MATCH (start:Symbol {qualified_name: $qname}) RETURN start", qname=start_name)
        record = await res.single()
        if not record:
            return []
        start_node = record["start"]
        query = BLAST_RADIUS_APOC
        result = await session.run(query, start=start_node, max_depth=max_depth)
    else:
        query = BLAST_RADIUS_NATIVE
        logger.warning("APOC not available — using native Cypher traversal")
        result = await session.run(query, qname=start_name, max_depth=max_depth)
        
    return await result.data()
