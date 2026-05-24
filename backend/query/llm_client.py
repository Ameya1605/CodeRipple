"""
LLM client — Fix #5: Properly splits system/user roles from message list.
"""
import logging
from typing import AsyncGenerator, List, Dict, Tuple
from backend.ai.factory import analysis_router

logger = logging.getLogger(__name__)


def _split_messages(messages: List[Dict[str, str]]) -> Tuple[str, str]:
    """
    Fix #5: Extract system and user content from message list.
    Handles: missing system role, multiple user turns, malformed entries.
    """
    system_parts: List[str] = []
    user_parts: List[str] = []

    for m in messages:
        role = m.get("role", "").lower()
        content = m.get("content", "")
        if role == "system":
            system_parts.append(content)
        elif role in ("user", "human"):
            user_parts.append(content)
        else:
            # Unknown role — append to user as a fallback, log a warning
            logger.warning(f"Unknown message role '{role}' — treating as user content")
            user_parts.append(content)

    return "\n\n".join(system_parts), "\n\n".join(user_parts)


async def call_llm_streaming(messages: list) -> AsyncGenerator[str, None]:
    try:
        system_instruction, user_message = _split_messages(messages)
        
        if not system_instruction:
            logger.warning("No system instruction found in messages — LLM quality may be degraded")
        
        async for chunk in analysis_router.analyze_stream(
            system=system_instruction,
            user=user_message,
            temperature=0.2
        ):
            yield chunk
    except Exception as e:
        logger.error(f"LLM streaming failed: {e}")
        yield f"\n\n[Error: Analysis failed: {e}]"
