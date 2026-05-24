"""
Backend configuration — loaded from environment variables with .env support.

Fix #15: Auto-loads .env file via python-dotenv.
Fix #2:  Environment-aware Redis defaults.
F-8:     Validates required variables at startup.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root (Fix #15)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

# ── Runtime Environment ──────────────────────────────────────────────────────
ENVIRONMENT             = os.getenv("ENVIRONMENT", "development")

# ── Databases ────────────────────────────────────────────────────────────────
QDRANT_URL              = os.getenv("QDRANT_URL", "http://localhost:6333")
NEO4J_URI               = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER              = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD          = os.getenv("NEO4J_PASSWORD", "devpassword")

# ── Auth ─────────────────────────────────────────────────────────────────────
SECRET_KEY              = os.getenv("SECRET_KEY", "super-secret-default-key")
AUTH_ENABLED            = os.getenv("AUTH_ENABLED", "False").lower() in ("true", "1", "t")
AUTH_DEV_BYPASS_TOKEN   = os.getenv("AUTH_DEV_BYPASS_TOKEN", "dev-local-token")

# ── Redis / Celery (Fix #2: environment-aware defaults) ──────────────────────
REDIS_URL               = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL       = os.getenv("CELERY_BROKER_URL", "")
CELERY_RESULT_BACKEND   = os.getenv("CELERY_RESULT_BACKEND", "")
effective_broker_url    = CELERY_BROKER_URL or REDIS_URL
effective_result_backend= CELERY_RESULT_BACKEND or REDIS_URL

# ── API Keys ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY          = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY       = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY          = os.getenv("GEMINI_API_KEY")
GITHUB_WEBHOOK_SECRET   = os.getenv("GITHUB_WEBHOOK_SECRET")

# ── AI Routing Configuration ─────────────────────────────────────────────────
LLM_PRIMARY             = os.getenv("LLM_PRIMARY", "gemini") # gemini | anthropic | openai | ollama
LLM_SECONDARY           = os.getenv("LLM_SECONDARY")         # optional, enables dual-model consensus
EMBEDDING_PROVIDER      = os.getenv("EMBEDDING_PROVIDER", "gemini") # gemini | openai | ollama

# ── Model IDs ────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL         = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL            = os.getenv("OLLAMA_MODEL", "codellama")
OLLAMA_EMBED_MODEL      = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")

GEMINI_MODEL            = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBED_MODEL      = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")
EMBEDDING_DIM           = 768  # Gemini embedding-001 dimension


ANTHROPIC_MODEL         = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")

OPENAI_MODEL            = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_EMBED_MODEL      = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# ── Collection Names ─────────────────────────────────────────────────────────
COLLECTION_SYMBOLS      = "dep_impact_symbols_v2"
COLLECTION_CONTRACTS    = "dep_impact_contracts_v2"
COLLECTION_ANALYSES     = "dep_impact_analyses_v2"

# ── Retrieval & Reranking Defaults ───────────────────────────────────────────
MAX_RETRIEVED           = 25
PHASE_A_CANDIDATES      = 50
PHASE_A_MIN_SCORE       = 0.60
RERANK_VECTOR_W         = 0.60
RERANK_GRAPH_W          = 0.25
RERANK_RISK_W           = 0.15
RISK_SCORE_WEIGHTS      = {
    "churn": 0.25, "fan_out": 0.25,
    "coverage_gap": 0.20, "critical_path": 0.20, "break_history": 0.10
}


# ── Startup Validation (F-8) ────────────────────────────────────────────────

def validate_config() -> None:
    """
    Call this at application startup. Logs warnings for missing config
    but does NOT crash in development mode — just warns loudly.
    """
    import logging
    _logger = logging.getLogger(__name__)

    checks = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "NEO4J_URI": NEO4J_URI,
        "QDRANT_URL": QDRANT_URL,
        "REDIS_URL": REDIS_URL,
    }

    missing = []
    for var, val in checks.items():
        if not val or val.startswith("your-"):
            missing.append(var)

    if missing:
        msg = (
            f"Missing or placeholder values for: {', '.join(missing)}. "
            f"Copy .env.example to .env and fill in the values. "
            f"See README.md for setup instructions."
        )
        if ENVIRONMENT == "production":
            raise EnvironmentError(msg)
        else:
            _logger.warning(f"Config warning (non-fatal in {ENVIRONMENT}): {msg}")
