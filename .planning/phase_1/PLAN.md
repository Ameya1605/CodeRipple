# Phase 1: AI Provider Abstraction

## Objective
Eliminate single-vendor lock-in by creating a provider interface for LLMs and Embeddings. Implement concrete providers for Gemini, Anthropic, OpenAI, and Ollama.

## Task List
1. [ ] **Infrastructure**: Add `ollama` service to `docker-compose.yml`.
2. [ ] **Core Abstraction**: Create `backend/ai/providers/base.py` with `LLMProvider` and `EmbeddingProvider` abstract classes.
3. [ ] **Gemini Provider**: Implement `backend/ai/providers/gemini.py` (migrating current logic).
4. [ ] **Anthropic Provider**: Implement `backend/ai/providers/anthropic.py` using `anthropic` SDK.
5. [ ] **OpenAI Provider**: Implement `backend/ai/providers/openai.py` using `openai` SDK.
6. [ ] **Ollama Provider**: Implement `backend/ai/providers/ollama.py` using `httpx` async client.
7. [ ] **Consensus Router**: Create `backend/ai/router.py` with `AnalysisRouter` for dual-model consensus.
8. [ ] **Configuration**: Update `backend/config.py` to support `LLM_PRIMARY`, `LLM_SECONDARY`, and `EMBEDDING_PROVIDER`.
9. [ ] **Integration**: Update `backend/main.py` and other services to use the new `AnalysisRouter`.

## UAT Criteria
- [ ] `docker-compose up` starts all services including Ollama.
- [ ] Switching `LLM_PRIMARY` in `.env` to `ollama` or `openai` produces valid analysis.
- [ ] Dual-model consensus (e.g., Gemini + Ollama) flags disagreements correctly.
- [ ] Unit tests for all providers pass.

## Verification
- Run `pytest tests/unit/test_ai_providers.py`.
- Verify `.env` configuration behavior.
