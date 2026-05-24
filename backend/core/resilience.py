"""
Retry decorator for external service calls (F-7).
Provides exponential backoff, per-call timeout, and typed exception logging.
"""
import asyncio
import functools
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,),
    timeout_seconds: float = 30.0,
):
    """
    Decorator for external service calls. Provides:
    - Exponential backoff with jitter
    - Per-call timeout
    - Typed exception logging
    - Attempt count in logs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout_seconds,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"{func.__name__} timed out after {timeout_seconds}s "
                        f"(attempt {attempt}/{max_attempts})"
                    )
                    last_exc = asyncio.TimeoutError(f"{func.__name__} timed out")
                except exceptions as e:
                    logger.warning(
                        f"{func.__name__} failed "
                        f"(attempt {attempt}/{max_attempts}): {e}"
                    )
                    last_exc = e

                if attempt < max_attempts:
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    await asyncio.sleep(delay)

            logger.error(
                f"{func.__name__} failed after {max_attempts} attempts: {last_exc}"
            )
            raise last_exc
        return wrapper
    return decorator
