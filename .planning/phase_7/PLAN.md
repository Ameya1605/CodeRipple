# Phase 7: Time-Travel Analysis

## Objective
Implement a temporal graph in Neo4j to track symbol evolution across commits, enabling "soft deletes" and historical impact analysis.

## Task List
1. [ ] **Soft Deletes**: Update `DeltaIndexer` to mark symbols as `deleted_at_commit` instead of detached deletion.
2. [ ] **Versioned Nodes**: Update Neo4j schema to support `:SymbolVersion` nodes linked by `:EVOLVED_FROM`.
3. [ ] **Temporal Querying**: Update retrieval logic to only fetch symbols active at the current commit.
4. [ ] **History API**: Create `GET /api/symbols/history/{qname}` to retrieve the evolution of a symbol and its historical risk scores.
5. [ ] **Impact Regression**: Compare the current blast radius with a historical baseline to detect "risk creep".

## UAT Criteria
- [ ] Deleted symbols are not returned in standard retrieval but exist in history.
- [ ] Analysis shows "Risk Creep: +15%" if the current change affects more critical paths than the previous version.
- [ ] Neo4j queries filter by `active: true` or `deleted_at_commit IS NULL`.
