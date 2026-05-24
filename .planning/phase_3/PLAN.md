# Phase 3: Contract Diff Language (CDL)

## Objective
Define a machine-readable schema for symbol contracts and implement deterministic breaking change detection.

## Task List
1. [ ] **Contract Schema**: Create `backend/intelligence/cdl/schema.py` with `SymbolContract` and `ContractDelta` models.
2. [ ] **Contract Extraction**: Update AST parsers to extract full `SymbolContract` data (params, return types, exceptions).
3. [ ] **Deterministic Differ**: Create `backend/intelligence/cdl/differ.py` to compare contracts and detect breaking changes (no LLM).
4. [ ] **SemVer Logic**: Implement automated `suggest_semver` based on the detected changes.
5. [ ] **Integration**: Store contracts in Qdrant/Postgres and surface `cdl_delta` in the analysis API response.

## UAT Criteria
- [ ] Breaking changes (e.g., removing a required parameter) are detected 100% deterministically.
- [ ] Non-breaking changes (e.g., adding an optional parameter) suggest `MINOR` version bump.
- [ ] API response includes a structured `cdl_delta` block with `is_breaking` and `semver_suggestion`.
