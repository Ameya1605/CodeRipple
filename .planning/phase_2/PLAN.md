# Phase 2: Delta Indexer

## Objective
Implement sub-second incremental indexing to only re-index changed symbols and their immediate neighbors.

## Task List
1. [ ] **Postgres Update**: Add `file_hash` column to the symbols/files table to track changes.
2. [ ] **Delta Indexer Logic**: Create `backend/indexer/delta_indexer.py` with `index_file_delta` method.
3. [ ] **Symbol Refresh**: Logic to re-embed and upsert modified symbols in Qdrant/Neo4j.
4. [ ] **Soft Delete**: Mark deleted symbols with `deleted_at_commit` in Neo4j.
5. [ ] **API Endpoint**: Create `POST /api/index/delta` for incremental updates.
6. [ ] **VS Code Extension**: Add file watcher to call the delta indexer on save.
7. [ ] **Git Hook**: Add pre-commit hook to trigger delta indexing.

## UAT Criteria
- [ ] Incremental indexing of a single file completes in <500ms.
- [ ] Modified symbols are correctly updated in both Qdrant and Neo4j.
- [ ] Deleted symbols are marked as stale/deleted.
- [ ] VS Code status bar confirms "Index updated" on file save.
