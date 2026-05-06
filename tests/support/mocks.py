"""
Test doubles for infrastructure services.

These mocks are used exclusively in the test suite to avoid depending on
real external services (CDN, MongoDB, WebSocket) in unit tests.
"""

import asyncio
import logging

from src.core.interfaces import NotificationService

logger = logging.getLogger(__name__)


class WebSocketNotifierMock(NotificationService):
    """In-memory mock that simulates a WebSocket notifier without any I/O."""

    async def notify_status(
        self, user_id: str, image_id: str, status: str, progress: int = 0, message: str = ""
    ) -> None:
        logger.info(
            "Simulating WebSocket emit to user %s: [Image %s] Status: %s (%d%%) - %s",
            user_id,
            image_id,
            status,
            progress,
            message,
        )
        await asyncio.sleep(0.05)
