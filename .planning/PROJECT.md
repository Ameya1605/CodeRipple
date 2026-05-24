# Dependency Impact Analyzer: Full Upgrade

A RAG-powered static analysis platform that assesses the blast radius and risk profile of codebase changes. 

## Context
The project is being upgraded to a production-grade system with multi-model support, deterministic contract diffing, and deep AST coverage. 

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, Celery + Redis, Tree-sitter
- **AI**: Gemini 1.5 Pro, Anthropic Claude, OpenAI GPT-4o, Ollama (Local)
- **Vector DB**: Qdrant
- **Graph DB**: Neo4j
- **Relational DB**: PostgreSQL
- **Frontend**: React + Vite, Vanilla CSS, Recharts, WebSockets
- **Dev Tooling**: VS Code Extension, Docker Compose, Makefile

## Core Objectives
1. Eliminate single-vendor lock-in via a robust AI Abstraction Layer.
2. Ensure grounded generation by pre-verifying symbols in the graph.
3. Implement deterministic Contract Diff Language (CDL).
4. Achieve sub-second incremental indexing.
5. Provide actionable insights via PR bots and automated test generation.
