"""
Process-safe context storage using Redis.
Replaces the in-process router.fallback_store anti-pattern (Fix #10).
"""
import json
import logging
import redis.asyncio as aioredis
from backend.config import REDIS_URL

logger = logging.getLogger(__name__)

CONTEXT_TTL_SECONDS = 3600  # 1 hour — enough for any analysis to complete


async def save_context(request_id: str, ctx: dict) -> bool:
    """Save analysis context to Redis. Returns True on success."""
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        key = f"dia:context:{request_id}"
        await r.setex(key, CONTEXT_TTL_SECONDS, json.dumps(ctx))
        return True
    except Exception as e:
        logger.error(f"Failed to save context {request_id}: {e}")
        return False
    finally:
        await r.aclose()


async def load_context(request_id: str) -> dict | None:
    """Load analysis context from Redis. Returns None if missing or expired."""
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        key = f"dia:context:{request_id}"
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.error(f"Failed to load context {request_id}: {e}")
        return None
    finally:
        await r.aclose()


async def delete_context(request_id: str) -> None:
    """Clean up context after analysis completes."""
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.delete(f"dia:context:{request_id}")
    except Exception:
        pass
    finally:
        await r.aclose()
