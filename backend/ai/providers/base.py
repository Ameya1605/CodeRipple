from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator

@dataclass
class AnalysisResponse:
    content: str
    model: str
    provider: str
    confidence: float  # 0.0–1.0, derived from token logprobs where available
    raw: dict[str, Any]

@dataclass
class EmbeddingResponse:
    vector: list[float]
    model: str
    provider: str
    dimensions: int

class LLMProvider(ABC):
    @abstractmethod
    async def analyze(self, system: str, user: str, temperature: float = 0.1) -> AnalysisResponse:
        """Standard non-streaming analysis."""
        ...

    @abstractmethod
    async def analyze_stream(self, system: str, user: str, temperature: float = 0.1) -> AsyncGenerator[str, None]:
        """Streaming analysis."""
        ...

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResponse:
        """Embed a single string."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        """Embed a batch of strings."""
        ...
