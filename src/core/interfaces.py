from typing import Protocol
from src.core.events import ProcessingOptions, ProcessingMetadata


class ImageProcessingService(Protocol):
    async def process_image(
        self, raw_image_data: bytes, options: ProcessingOptions
    ) -> tuple[bytes, ProcessingMetadata]:
        """
        Processes a raw image based on the given options using MediaPipe or similar.
        Returns the processed image bytes and the resulting metadata.
        """
        ...


class StorageService(Protocol):
    async def upload_image(
        self, image_id: str, image_data: bytes, folder: str = "processed"
    ) -> str:
        """
        Uploads an image to a CDN or blob storage.
        Returns the public URL or storage path of the uploaded image.
        """
        ...

    async def download_image(self, storage_path: str) -> bytes:
        """
        Downloads a raw image from the CDN.
        """
        ...


class DatabaseRepository(Protocol):
    async def save_image_metadata(
        self,
        image_id: str,
        project_id: str,
        result_url: str,
        metadata: ProcessingMetadata,
    ) -> None:
        """
        Saves the final processed image metadata into the database (e.g., MongoDB).
        """
        ...


class NotificationService(Protocol):
    async def notify_status(
        self, user_id: str, image_id: str, status: str, progress: int = 0, message: str = ""
    ) -> None:
        """
        Sends a real-time notification to the user via WebSockets.
        """
        ...
