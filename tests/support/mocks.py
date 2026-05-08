"""
Test doubles for infrastructure services.

These mocks are used exclusively in the test suite to avoid depending on
real external services (CDN, MongoDB, WebSocket) in unit tests.
"""

import asyncio
import logging

from src.core.interfaces import NotificationService, StorageService

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


class CDNStorageMock(StorageService):
    """
    CDN mock for unit tests. 
    Does not make real calls to Cloudinary.
    """

    def __init__(self):
        self.uploaded: list[dict] = []
        self.downloaded: list[str] = []

    async def upload_image(
        self, image_id: str, image_data: bytes, folder: str = "processed"
    ) -> str:
        self.uploaded.append({"image_id": image_id, "folder": folder})
        fake_url = f"https://res.cloudinary.com/mock/{folder}/{image_id}.png"
        logger.info(f"[Mock CDN] upload_image — {fake_url}")
        return fake_url

    async def download_image(self, storage_path: str) -> bytes:
        self.downloaded.append(storage_path)
        logger.info(f"[Mock CDN] download_image — {storage_path}")
        return b"mock-image-data"