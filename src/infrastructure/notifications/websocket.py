import asyncio
import logging
from src.core.interfaces import NotificationService

logger = logging.getLogger(__name__)


class WebSocketNotifierMock(NotificationService):
    async def notify_status(
        self, user_id: str, image_id: str, status: str, message: str = ""
    ) -> None:
        logger.info(
            f"Simulating WebSocket emit to user {user_id}: [Image {image_id}] Status: {status} - {message}"
        )
        await asyncio.sleep(0.05)
