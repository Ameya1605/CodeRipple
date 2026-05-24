# Phase 4: Grounded Generation (RAG+)

## Objective
Implement a multi-stage retrieval pipeline (Vector + Graph + Re-ranking) to provide the LLM with the most relevant context for impact analysis.

## Task List
1. [ ] **Hybrid Search**: Combine Qdrant vector search with Neo4j "neighbor of neighbor" (2-hop) expansion.
2. [ ] **Cross-Repository Retrieval**: Expand search to all repositories in the database if the changed symbol is part of a shared library/contract.
3. [ ] **Reranking Engine**: Implement `backend/retrieval/reranker.py` to score candidates based on:
    - Vector similarity.
    - Graph distance (closer = more relevant).
    - Risk score of the dependent (higher risk = more important to analyze).
4. [ ] **Context Truncation**: Logic to fit the most relevant candidates into the LLM context window while preserving the most critical ones.
5. [ ] **Pre-prompt Verification**: Add a step for the LLM to verify if the retrieved context is sufficient before starting the analysis.

## UAT Criteria
- [ ] Retrieval includes symbols from external repositories that depend on the changed contract.
- [ ] Reranking prioritizes "Critical Path" symbols (e.g., entry points) even if vector similarity is lower.
- [ ] Analysis quality improves (less hallucinations about missing context).
