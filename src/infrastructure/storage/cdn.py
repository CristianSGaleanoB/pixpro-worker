import asyncio
import logging
from typing import cast
from src.core.interfaces import StorageService
import cloudinary
import cloudinary.uploader
import cloudinary.api
import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class CloudinaryCDNStorage(StorageService):
    """
    Cloudinary real Adapter.
    """

    def __init__(self):
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,  # Siempre HTTPS
        )
        logger.info("CloudinaryCDNStorage initialized")

    async def download_image(self, storage_path: str) -> bytes:
        """
        Downloads an image from its public URL on Cloudinary.
        storage_path is the secure_url that the API saved.
        """
        logger.info(f"Downloading image from CDN: {storage_path}")

        async with httpx.AsyncClient() as client:
            response = await client.get(storage_path)
            response.raise_for_status()

        logger.info(f"Image downloaded — size: {len(response.content)} bytes")
        return response.content

    async def upload_image(
        self, image_id: str, image_data: bytes, folder: str = "processed"
    ) -> str:
        """
        Uploads the processed image to Cloudinary.
        The image_id and folder define the path in Cloudinary (e.g., pixpro/processed/{imageId}).
        Returns the public secure_url.
        """
        logger.info(
            f"Uploading processed image to CDN — folder: {folder}, image_id: {image_id}"
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.upload(
                image_data,
                folder=f"pixpro/{folder}",
                public_id=image_id,
                resource_type="image",
                overwrite=True,
            ),
        )

        url = cast(str, result["secure_url"])
        logger.info(f"Processed image uploaded to CDN — url: {url}")
        return url
