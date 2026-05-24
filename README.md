# CodeRipple(Dependency Impact Analyzer) (v2.0 Production Platform)

A highly accurate, multi-model, RAG-powered static analysis platform designed to assess the blast radius, contract changes, and downstream risks of codebase modifications. It leverages hybrid retrieval (Vector/Graph), precise AST parsing, and advanced LLM reasoning to ensure robust change safety.

---

## Architecture & Technology Stack

The platform runs as a fully containerized orchestration suite using **Docker Compose**:
- **FastAPI Core Service**: REST API and live WebSocket stream orchestration.
- **Qdrant Vector Database**: Manages AST code chunk semantic embeddings and documentation context.
- **Neo4j Graph Database**: Stores precise call graphs, inheritance trees, and import structures.
- **PostgreSQL**: Relational storage for repository metadata, persistent review attributions, and Webhook logs.
- **Redis & Celery**: Distributed job queue handling asynchronous codebase indexing and background impact computation tasks.
- **React 19 Frontend**: Glassmorphism aesthetic dark-mode dashboard featuring interactive graph maps (`ReactFlow`) and analytical impact distribution metrics (`Recharts`).
- **Multi-Model Support**: Native integrations for **Google Gemini (1.5 Pro / Flash)** and **Ollama** local inference fallback.

---

## Quickstart & Installation

### 1. Environment Setup
Copy the environment template to create your `.env` configuration file:
```bash
cp .env.example .env
```
Ensure your `GEMINI_API_KEY` is configured inside `.env`.

### 2. Launch the Platform Orchestration
Start the entire stack using Docker Compose:
```bash
docker-compose up --build -d
```

### 3. Verify System Operation
- **API Swagger Documentation**: [http://localhost:8080/docs](http://localhost:8080/docs)
- **Sentinel AI Web Dashboard**: [http://localhost:5173/dashboard](http://localhost:5173/dashboard)
- **Neo4j Browser Console**: [http://localhost:7474](http://localhost:7474) *(Credentials: `neo4j` / `devpassword`)*

---

## How to Use the Platform

### Option A: Interactive Web Dashboard
1. Navigate to **[http://localhost:5173/dashboard](http://localhost:5173/dashboard)**.
2. Enter the target symbol or function name (e.g., `calculate_impact`) in the top search bar.
3. Click **Analyze Impact** to trigger live reasoning over WebSockets. Watch the real-time stream update the reasoning engine, extract recommended test coverage gaps, and dynamically adjust risk distributions.

### Option B: Command-Line Interface (CLI)
You can trigger indexing and analysis directly via terminal tools. Ensure your Python environment has dependencies installed (`pip install -r requirements.txt`).

#### **1. Index a Repository**
Extracts AST definitions, builds the call graph in Neo4j, and generates semantic vector chunks in Qdrant:
```bash
python scripts/index.py --repo /path/to/target/repository --repo-id target-repo-v1
```

#### **2. Analyze Specific Symbol Modifications**
Evaluate the downstream blast radius resulting from specific symbol logic changes:
```bash
python scripts/analyze.py symbol --name calculate_impact --change "Refactored parsing heuristics" --repo /path/to/target/repository
```

#### **3. Analyze Local Uncommitted Git Diffs**
Automatically scans unstaged/staged files via `git diff` to compute change risk tiers before committing:
```bash
python scripts/analyze.py diff --file src/utils.py --repo /path/to/target/repository
```
*Append `--format json` to receive clean structure buffers intended for automated CI/CD gating pipelines.*

---

## Automated CI/CD Integrations

- **GitHub PR Bot Integration**: Trigger dynamic pull request analysis evaluations via exposed webhooks mounted on `/api/v1/webhooks/github`.
- **Git Post-Commit Hook**: Automatically queues local background index cycles after code commits using the custom hook template located at `scripts/hooks/post-commit`.

---

## Learning Feedback Loop (RLHF)

Sentinel AI features a self-improving intelligence layer:
- **Human-in-the-Loop**: Users can flag AI results as "Correct" or "False Positive" directly in the dashboard.
- **Few-Shot Learning**: The system automatically injects corrected examples into future analysis prompts to prevent repeating mistakes.
- **Weight Optimization**: The reranking engine (Vector vs. Graph vs. Risk) dynamically suggests weight adjustments based on the aggregate false-positive rate.
- **Accuracy Metrics**: Track the platform's precision over time via the `/api/v1/health/accuracy` endpoint.
