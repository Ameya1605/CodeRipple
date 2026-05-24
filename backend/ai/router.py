import asyncio
import logging
from typing import AsyncGenerator
from backend.ai.providers.base import LLMProvider, AnalysisResponse

logger = logging.getLogger(__name__)

class AnalysisRouter:
    """
    Routes analysis requests through one or two providers.
    When dual=True, runs both providers concurrently and compares risk assessments.
    """
    def __init__(self, primary: LLMProvider, secondary: LLMProvider | None = None):
        self.primary = primary
        self.secondary = secondary

    async def analyze_with_consensus(
        self,
        system: str,
        user: str,
        temperature: float = 0.1,
        force_dual: bool = False
    ) -> AnalysisResponse:
        if not self.secondary or not force_dual:
            return await self.primary.analyze(system, user, temperature)

        # Run both in parallel
        tasks = [
            self.primary.analyze(system, user, temperature),
            self.secondary.analyze(system, user, temperature)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        primary_res = results[0] if not isinstance(results[0], Exception) else None
        secondary_res = results[1] if not isinstance(results[1], Exception) else None

        if primary_res and not secondary_res:
            return primary_res
        if not primary_res and secondary_res:
            return secondary_res
        if not primary_res and not secondary_res:
            raise results[0] # Re-raise primary exception if both failed

        # Both succeeded, implement simple consensus logic
        # For now, we just merge content if they are different or flag uncertainty
        # A more advanced version would parse risk scores and compare
        
        merged_content = primary_res.content
        if primary_res.content != secondary_res.content:
            merged_content += f"\n\n---\n**Secondary Model Analysis ({secondary_res.provider})**:\n{secondary_res.content}"
            
        return AnalysisResponse(
            content=merged_content,
            model=f"{primary_res.model} + {secondary_res.model}",
            provider="consensus",
            confidence=(primary_res.confidence + secondary_res.confidence) / 2,
            raw={"primary": primary_res.raw, "secondary": secondary_res.raw}
        )

    async def analyze_stream(self, system: str, user: str, temperature: float = 0.1) -> AsyncGenerator[str, None]:
        # Streaming currently only uses primary
        async for chunk in self.primary.analyze_stream(system, user, temperature):
            yield chunk
