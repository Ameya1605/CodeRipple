import logging
import json
import httpx
from typing import AsyncGenerator
from backend.ai.providers.base import LLMProvider, EmbeddingProvider, AnalysisResponse, EmbeddingResponse

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider, EmbeddingProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model_id: str = "codellama", embedding_model: str = "all-minilm"):
        self.base_url = base_url
        self.model_id = model_id
        self.embedding_model = embedding_model

    async def analyze(self, system: str, user: str, temperature: float = 0.1) -> AnalysisResponse:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model_id,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user}
                        ],
                        "options": {"temperature": temperature},
                        "stream": False
                    }
                )
                response.raise_for_status()
                data = response.json()
                return AnalysisResponse(
                    content=data["message"]["content"],
                    model=self.model_id,
                    provider="ollama",
                    confidence=1.0,
                    raw=data
                )
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            raise

    async def analyze_stream(self, system: str, user: str, temperature: float = 0.1) -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model_id,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user}
                        ],
                        "options": {"temperature": temperature},
                        "stream": True
                    }
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                            if data.get("done"):
                                break
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield f"\n\n[Error: Ollama Analysis failed: {e}]"

    async def embed(self, text: str) -> EmbeddingResponse:
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        results = []
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                for text in texts:
                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={
                            "model": self.embedding_model,
                            "prompt": text
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    results.append(EmbeddingResponse(
                        vector=data["embedding"],
                        model=self.embedding_model,
                        provider="ollama",
                        dimensions=len(data["embedding"])
                    ))
            return results
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise
