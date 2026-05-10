import asyncio
import logging
from typing import Callable, Any, Type, Tuple

logger = logging.getLogger(__name__)


async def retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    **kwargs,
) -> Any:
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(f"Max retries ({max_retries}) exhausted. Last error: {e}")
                raise e

            backoff = min(initial_backoff * (2**attempt), max_backoff)

            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {backoff}s..."
            )

            await asyncio.sleep(backoff)

    if last_exception:
        raise last_exception
