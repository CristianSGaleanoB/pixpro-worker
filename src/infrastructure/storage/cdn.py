import asyncio
import logging
from src.core.interfaces import StorageService

logger = logging.getLogger(__name__)

class CDNStorageMock(StorageService):
    async def upload_image(self, image_id: str, image_data: bytes, folder: str = "processed") -> str:
        logger.info(f"Simulating CDN upload for {image_id} (size: {len(image_data)} bytes)...")
        await asyncio.sleep(0.5)
        return f"https://cdn.example.com/assets/{folder}/{image_id}.jpg"
        
    async def download_image(self, storage_path: str) -> bytes:
        logger.info(f"Simulating CDN download from {storage_path}...")
        await asyncio.sleep(0.5)
        return b"MOCK_ORIGINAL_IMAGE_BYTES"
