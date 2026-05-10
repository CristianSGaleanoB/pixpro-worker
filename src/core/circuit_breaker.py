import time
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: tuple = (Exception,),
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._name = "CircuitBreaker"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"{self._name} state: OPEN → HALF_OPEN (testing recovery)")
                self._state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"{self._name} is OPEN - service unavailable")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    def _on_success(self):
        if self._state == CircuitState.HALF_OPEN:
            logger.info(f"{self._name} state: HALF_OPEN → CLOSED (recovered)")
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            logger.error(
                f"{self._name} state: {self._state.value.upper()} → OPEN "
                f"({self._failure_count} failures)"
            )
            self._state = CircuitState.OPEN

    @property
    def state(self) -> str:
        return self._state.value

    def reset(self):
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        logger.info(f"{self._name} manually reset to CLOSED")
