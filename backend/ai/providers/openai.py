import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI
from backend.ai.providers.base import LLMProvider, EmbeddingProvider, AnalysisResponse, EmbeddingResponse

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider, EmbeddingProvider):
    def __init__(self, api_key: str, model_id: str = "gpt-4o", embedding_model: str = "text-embedding-3-small"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_id = model_id
        self.embedding_model = embedding_model

    async def analyze(self, system: str, user: str, temperature: float = 0.1) -> AnalysisResponse:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=temperature
            )
            return AnalysisResponse(
                content=response.choices[0].message.content,
                model=self.model_id,
                provider="openai",
                confidence=1.0,
                raw=response.model_dump()
            )
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise

    async def analyze_stream(self, system: str, user: str, temperature: float = 0.1) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=temperature,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            yield f"\n\n[Error: OpenAI Analysis failed: {e}]"

    async def embed(self, text: str) -> EmbeddingResponse:
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [
                EmbeddingResponse(
                    vector=item.embedding,
                    model=self.embedding_model,
                    provider="openai",
                    dimensions=len(item.embedding)
                ) for item in response.data
            ]
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
