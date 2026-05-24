# Phase 8: Automated Test Gap Generation

## Objective
Automatically generate test skeletons for dependents that are impacted by a change but lack sufficient test coverage.

## Task List
1. [ ] **Coverage Engine**: Integrate with `pytest-cov` or `istanbul` to identify symbols with < 50% coverage.
2. [ ] **Skeleton Generator**: Create a prompt template for generating `pytest` or `vitest` skeletons based on the symbol's contract and implementation.
3. [ ] **Verification Loop**: Run the generated test to ensure it passes with the *current* code (proving it's a valid regression test).
4. [ ] **UI Integration**: Add a "Generate Tests" button in the Analysis dashboard next to impacted dependents.
5. [ ] **Batch Mode**: Generate a full test suite for a "High Risk" blast radius.

## UAT Criteria
- [ ] Analysis output includes a `test_gap_suggestions` array.
- [ ] Clicking "Generate" produces a valid `.py` or `.ts` test file.
- [ ] The generated test correctly mocks dependencies of the symbol being tested.
