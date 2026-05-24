import hashlib
import logging
import os
import tempfile
from typing import List, Dict, Any
from backend.indexer.schema import CodeChunk
from backend.indexer.parsers import parse_file
from backend.indexer.embedder import embed_chunks
from backend.indexer.vector_store import vector_store
from backend.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

class DeltaIndexer:
    def compute_file_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def index_file_delta(self, repo_id: str, repo_root: str, file_path: str, content: str) -> Dict[str, Any]:
        """
        Incrementally index a single file.
        """
        new_hash = self.compute_file_hash(content)
        
        # 1. Parse the new content
        # We use a temporary file to avoid overwriting the original file during parsing
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(file_path)[1], delete=False, mode='w', encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # We need to pass the repo_id to parse_file
            chunks = parse_file(tmp_path, repo_id)
            if not chunks:
                return {"status": "no_symbols", "count": 0}

            for chunk in chunks:
                chunk.file_path = file_path
                chunk.file_hash = new_hash
                # Assign a deterministic chunk_id if not already present
                if not chunk.chunk_id:
                    chunk.chunk_id = hashlib.md5(f"{repo_id}:{file_path}:{chunk.qualified_name}".encode()).hexdigest()

            # 2. Embed the new chunks
            await embed_chunks(chunks)

            # 3. Update Qdrant
            await vector_store.upsert_chunks(chunks)

            # 4. Update Neo4j
            await self._update_graph(repo_id, file_path, chunks)
            
            # 5. Implicit Edges
            from backend.indexer.implicit_graph import build_implicit_edges
            await build_implicit_edges(chunks)

            return {"status": "success", "count": len(chunks)}
        except Exception as e:
            logger.error(f"Delta indexing failed for {file_path}: {e}")
            raise
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def _update_graph(self, repo_id: str, file_path: str, new_chunks: List[CodeChunk]):
        """
        Update Neo4j: mark old symbols as deleted and add new versioned symbols.
        """
        async with neo4j_client.session() as session:
            # a. Soft delete old symbols for this file
            # Mark symbols as deleted_at_commit instead of deleting them
            current_commit = new_chunks[0].commit_hash if new_chunks[0].commit_hash else "HEAD"
            
            await session.run(
                """
                MATCH (s:Symbol {repo_id: $repo_id, file_path: $file_path})
                WHERE s.deleted_at_commit IS NULL
                SET s.deleted_at_commit = $commit, s.active = false
                """,
                repo_id=repo_id, file_path=file_path, commit=current_commit
            )

            # b. Create new symbols as active
            for chunk in new_chunks:
                props = chunk.model_dump(exclude={
                    "_embedding_vector", 
                    "risk_score_history", 
                    "diff_changes", 
                    "parameters",
                    "calls",
                    "called_by"
                })
                
                await session.run(
                    """
                    MERGE (s:Symbol {chunk_id: $chunk_id})
                    SET s += $props, s.repo_id = $repo_id, s.file_path = $file_path, 
                        s.active = true, s.deleted_at_commit = null
                    """,
                    chunk_id=chunk.chunk_id,
                    props=props,
                    repo_id=repo_id,
                    file_path=file_path
                )

            # c. Re-build edges for active symbols only
            for chunk in new_chunks:
                # Outbound calls
                for target_name in chunk.calls:
                    await session.run(
                        """
                        MATCH (src:Symbol {chunk_id: $src_id})
                        MATCH (target:Symbol {repo_id: $repo_id, active: true})
                        WHERE target.symbol_name = $target_name OR target.qualified_name = $target_name
                        MERGE (src)-[:CALLS]->(target)
                        """,
                        src_id=chunk.chunk_id, repo_id=repo_id, target_name=target_name
                    )
                
                # Inbound calls
                await session.run(
                    """
                    MATCH (target:Symbol {chunk_id: $target_id})
                    MATCH (src:Symbol {repo_id: $repo_id, active: true})
                    WHERE $symbol_name IN src.calls OR $qname IN src.calls
                    MERGE (src)-[:CALLS]->(target)
                    """,
                    target_id=chunk.chunk_id, repo_id=repo_id, 
                    symbol_name=chunk.symbol_name, qname=chunk.qualified_name
                )

delta_indexer = DeltaIndexer()
