import pytest
import asyncio
from src.core.retry_utils import retry_with_backoff


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    call_count = 0

    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Temporary failure")
        return "success"

    result = await retry_with_backoff(flaky_function, max_retries=3)

    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausts_max_retries():
    async def always_fails():
        raise ConnectionError("Permanent failure")

    with pytest.raises(ConnectionError):
        await retry_with_backoff(always_fails, max_retries=2)
