from backend import config
from backend.ai.providers.gemini import GeminiProvider
from backend.ai.providers.anthropic import AnthropicProvider
from backend.ai.providers.openai import OpenAIProvider
from backend.ai.providers.ollama import OllamaProvider
from backend.ai.router import AnalysisRouter

def get_llm_provider(name: str):
    if name == "gemini":
        return GeminiProvider(api_key=config.GEMINI_API_KEY, model_id=config.GEMINI_MODEL, embedding_model=config.GEMINI_EMBED_MODEL)
    elif name == "anthropic":
        return AnthropicProvider(api_key=config.ANTHROPIC_API_KEY, model_id=config.ANTHROPIC_MODEL)
    elif name == "openai":
        return OpenAIProvider(api_key=config.OPENAI_API_KEY, model_id=config.OPENAI_MODEL, embedding_model=config.OPENAI_EMBED_MODEL)
    elif name == "ollama":
        return OllamaProvider(base_url=config.OLLAMA_BASE_URL, model_id=config.OLLAMA_MODEL, embedding_model=config.OLLAMA_EMBED_MODEL)
    else:
        raise ValueError(f"Unknown LLM provider: {name}")

def get_embedding_provider(name: str):
    if name == "gemini":
        return GeminiProvider(api_key=config.GEMINI_API_KEY, embedding_model=config.GEMINI_EMBED_MODEL)
    elif name == "openai":
        return OpenAIProvider(api_key=config.OPENAI_API_KEY, embedding_model=config.OPENAI_EMBED_MODEL)
    elif name == "ollama":
        return OllamaProvider(base_url=config.OLLAMA_BASE_URL, embedding_model=config.OLLAMA_EMBED_MODEL)
    else:
        raise ValueError(f"Unknown embedding provider: {name}")

# Global instances
primary_llm = get_llm_provider(config.LLM_PRIMARY)
secondary_llm = get_llm_provider(config.LLM_SECONDARY) if config.LLM_SECONDARY else None
analysis_router = AnalysisRouter(primary=primary_llm, secondary=secondary_llm)

embedding_provider = get_embedding_provider(config.EMBEDDING_PROVIDER)
