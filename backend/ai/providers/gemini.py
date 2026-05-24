"""
Gemini AI provider — Fix #4: All embedding calls are now fully async.
"""
import asyncio
import logging
from typing import AsyncGenerator
from google import genai
from google.genai import types
from backend.ai.providers.base import LLMProvider, EmbeddingProvider, AnalysisResponse, EmbeddingResponse

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider, EmbeddingProvider):
    def __init__(self, api_key: str, model_id: str = "gemini-1.5-pro", embedding_model: str = "models/gemini-embedding-001"):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.embedding_model = embedding_model

    async def analyze(self, system: str, user: str, temperature: float = 0.1) -> AnalysisResponse:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
            )
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=user,
                config=config
            )
            return AnalysisResponse(
                content=response.text,
                model=self.model_id,
                provider="gemini",
                confidence=1.0, # Gemini doesn't easily expose confidence yet
                raw=response.model_dump()
            )
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            raise

    async def analyze_stream(self, system: str, user: str, temperature: float = 0.1) -> AsyncGenerator[str, None]:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
            )
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_id,
                contents=user,
                config=config
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            yield f"\n\n[Error: Gemini Analysis failed: {e}]"

    async def embed(self, text: str) -> EmbeddingResponse:
        """Fix #4: Single embedding — uses async client."""
        try:
            result = await self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            vector = result.embeddings[0].values
            return EmbeddingResponse(
                vector=vector,
                model=self.embedding_model,
                provider="gemini",
                dimensions=len(vector),
            )
        except Exception as e:
            logger.error(f"Gemini embed failed: {e}")
            raise

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        """
        Fix #4: Fully async batch embedding using asyncio.gather.
        Uses a semaphore to respect rate limits.
        """
        CONCURRENCY_LIMIT = 5
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        async def _embed_one(text: str) -> EmbeddingResponse:
            async with semaphore:
                return await self.embed(text)

        results = await asyncio.gather(
            *[_embed_one(t) for t in texts],
            return_exceptions=True,
        )

        # Replace failed embeddings with a zero vector rather than crashing the batch
        from backend.config import EMBEDDING_DIM
        fixed = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.error(f"Embedding failed for text[{i}]: {r}")
                fixed.append(EmbeddingResponse(
                    vector=[0.0] * EMBEDDING_DIM,
                    model=self.embedding_model,
                    provider="gemini",
                    dimensions=EMBEDDING_DIM,
                ))
            else:
                fixed.append(r)
        return fixed
