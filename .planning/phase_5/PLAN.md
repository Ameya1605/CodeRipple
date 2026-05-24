# Phase 5: Deep AST Coverage

## Objective
Enhance AST parsers to handle complex language features (decorators, type aliases, generics) and improve the accuracy of the call graph.

## Task List
1. [ ] **Decorator Analysis**: Update Python parser to track decorators (e.g., `@app.route`, `@celery.task`) and link them to entry points.
2. [ ] **TypeScript Types**: Update TS parser to extract interface and type alias relationships (e.g., `implements`, `extends`).
3. [ ] **Go Interface Satisfaction**: Implement logic to detect when a Go struct implicitly satisfies an interface.
4. [ ] **Java Annotations**: Extract Spring/JAX-RS annotations to identify REST endpoints.
5. [ ] **Cross-Language Calls**: Basic support for detecting calls across languages (e.g., Python calling a Go microservice via `requests`).

## UAT Criteria
- [ ] Symbols decorated with `@app.route` are automatically marked as `is_on_critical_path`.
- [ ] TypeScript interfaces show "Implementors" in the analysis UI.
- [ ] Changing a Go interface correctly identifies all implementing structs as affected.
