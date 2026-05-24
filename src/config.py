import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "dep_impact_v1"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")

# Provider-specific defaults
if LLM_PROVIDER == "gemini":
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")
    EMBEDDING_DIM = 3072
    LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-1.5-pro")
else:
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIM = 1536
    LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o")

MAX_RETRIEVED = 20
PHASE1_CANDIDATES = 50
PHASE1_MIN_SCORE = 0.60
RERANK_VECTOR_WEIGHT = 0.7
RERANK_GRAPH_WEIGHT = 0.3
