import logging
from typing import AsyncGenerator
from anthropic import AsyncAnthropic
from backend.ai.providers.base import LLMProvider, AnalysisResponse

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model_id: str = "claude-3-5-sonnet-20240620"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model_id = model_id

    async def analyze(self, system: str, user: str, temperature: float = 0.1) -> AnalysisResponse:
        try:
            response = await self.client.messages.create(
                model=self.model_id,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user}],
                temperature=temperature
            )
            return AnalysisResponse(
                content=response.content[0].text,
                model=self.model_id,
                provider="anthropic",
                confidence=1.0,
                raw=response.model_dump()
            )
        except Exception as e:
            logger.error(f"Anthropic analysis failed: {e}")
            raise

    async def analyze_stream(self, system: str, user: str, temperature: float = 0.1) -> AsyncGenerator[str, None]:
        try:
            async with self.client.messages.stream(
                model=self.model_id,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user}],
                temperature=temperature
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            yield f"\n\n[Error: Anthropic Analysis failed: {e}]"
