import logging
from typing import List
from backend.indexer.schema import CodeChunk
from backend.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

async def build_implicit_edges(chunks: List[CodeChunk]):
    """
    Creates implicit edges in Neo4j based on shared env vars or strings.
    """
    async with neo4j_client.session() as session:
        for chunk in chunks:
            if not chunk.contract_data or "implicit_deps" not in chunk.contract_data:
                continue
            
            for dep in chunk.contract_data["implicit_deps"]:
                # Create a :Dependency node for the shared resource (env var or string)
                # and link the symbol to it.
                await session.run(
                    """
                    MERGE (d:Dependency {name: $dep_name})
                    WITH d
                    MATCH (s:Symbol {chunk_id: $chunk_id})
                    MERGE (s)-[:DEPENDS_ON_SEMANTIC]->(d)
                    """,
                    dep_name=dep,
                    chunk_id=chunk.chunk_id
                )
    logger.info(f"Built implicit edges for {len(chunks)} chunks")
