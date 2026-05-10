import asyncio
import logging
from src.core.interfaces import StorageService

logger = logging.getLogger(__name__)


class MockCDNStorage(StorageService):
    """
    Mock CDN storage for development/testing.

    Implements StorageService without making real HTTP calls.
    Returns dummy data on download and fake URLs on upload,
    so the digestion pipeline can run without Cloudinary credentials.
    """

    async def download_image(self, storage_path: str) -> bytes:
        logger.info(f"[MockCDN] download_image — {storage_path}")
        await asyncio.sleep(0.05)
        return b"mock-image-data"

    async def upload_image(
        self, image_id: str, image_data: bytes, folder: str = "processed"
    ) -> str:
        fake_url = f"https://res.cloudinary.com/mock/{folder}/{image_id}.png"
        logger.info(f"[MockCDN] upload_image — {fake_url}")
        await asyncio.sleep(0.05)
        return fake_url
