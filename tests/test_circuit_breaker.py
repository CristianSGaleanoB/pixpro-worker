import pytest
import time
import asyncio
from src.core.circuit_breaker import CircuitBreaker


@pytest.mark.asyncio
async def test_circuit_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

    async def always_fails():
        raise ConnectionError("Service down")

    for _ in range(3):
        try:
            await cb.call(always_fails)
        except:
            pass

    assert cb.state == "open"

    with pytest.raises(Exception, match="is OPEN"):
        await cb.call(always_fails)


@pytest.mark.asyncio
async def test_circuit_recovers_after_timeout():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)

    async def fails():
        raise ConnectionError("Down")

    async def succeeds():
        return "ok"

    for _ in range(2):
        try:
            await cb.call(fails)
        except:
            pass

    assert cb.state == "open"

    await asyncio.sleep(0.6)

    result = await cb.call(succeeds)
    assert result == "ok"
    assert cb.state == "closed"
