# Requirements: Dependency Impact Analyzer Upgrade

## 1. AI Abstraction Layer
- Base provider interface for LLM and Embeddings.
- Concrete providers: Gemini, Anthropic, OpenAI, Ollama.
- Dual-model consensus engine for risk assessment validation.
- Configurable via environment variables.

## 2. Grounded Generation
- Pre-prompt verification of symbols and call paths in Neo4j.
- Injected XML-tagged "grounded facts" block.
- Explicit instructions to restrict LLM references to verified symbols.

## 3. Deep AST Coverage
- TypeScript: Generics, Decorators, Dynamic imports, Barrel re-exports, Conditional exports, Interface merging.
- Python: `__import__`, `importlib`, Dataclass/Pydantic fields, `__all__`, Monkey-patching, Properties.
- New edge types in Neo4j (CALLS, IMPORTS, EXTENDS, etc.).

## 4. Feedback Loop
- Celery task to process user feedback.
- Auto-remediation for low-rated analyses.
- Risk weight adjustment based on patterns.

## 5. Contract Diff Language (CDL)
- Machine-readable schema for symbol contracts.
- Deterministic diffing (param changes, return types, exceptions, etc.).
- Automated SemVer suggestions.

## 6. Time-Travel Analysis
- Versioning (commit_sha) for all nodes and edges in Neo4j.
- Graph diffing between commits.
- Symbol contract history timeline.

## 7. Automated Test Generation
- Generate actual test stubs (pytest/jest) for high-risk uncovered paths.
- VS Code "QuickFix" integration.

## 8. PR Bot Integration
- GitHub/GitLab webhook handlers.
- Automated PR comments with risk summaries and graphs.

## 9. Reviewer Attribution
- Git blame analysis to identify downstream component owners.
- Suggest reviewers in PR comments.

## 10. Delta Indexer
- Sub-second incremental indexing for single files.
- VS Code file watcher integration.
- Git pre-commit hook support.

## 11. Health Scoring Dashboard
- Repo-level metrics: coupling, coverage, risk trends.
- Recharts-based frontend dashboard.
- LLM-generated refactoring recommendations.

## 12. Semantic Edge Graph
- Implicit dependencies: shared types, env vars, event buses, shared config.
