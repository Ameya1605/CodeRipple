# Phase 6: Semantic Edge Graph

## Objective
Detect implicit dependencies that aren't visible through direct function calls (e.g., event listeners, environment variable shared usage, database schema coupling).

## Task List
1. [ ] **Implicit Call Detection**: Logic to link symbols via "semantic similarity" if they both use the same unique string literals or env vars.
2. [ ] **Event/Topic Mapping**: Track usage of `EventEmitter`, `PubSub`, or `Kafka` topics to link producers and consumers.
3. [ ] **Shared Schema Coupling**: Link symbols that both perform queries on the same database table/collection.
4. [ ] **Relationship Scoring**: Assign a "semantic weight" to these implicit edges in Neo4j.
5. [ ] **UI Visualization**: Update the call graph visualization to show implicit edges with a dashed line.

## UAT Criteria
- [ ] Changing a producer for a Kafka topic correctly identifies consumers in other repositories as "Affected (Implicit)".
- [ ] Changing an environment variable key identifies all symbols reading that key across the codebase.
- [ ] Semantic edges contribute to the Reranking score in the retrieval pipeline.
