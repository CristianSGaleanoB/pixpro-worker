import logging
from src.core.events import ImageUploadedEvent, ImageProcessedEvent
from src.core.interfaces import (
    ImageProcessingService,
    StorageService,
    DatabaseRepository,
    NotificationService,
)

logger = logging.getLogger(__name__)


class DigestionPipeline:
    def __init__(
        self,
        processor: ImageProcessingService,
        storage: StorageService,
        database: DatabaseRepository,
        notifier: NotificationService,
    ):
        self.processor = processor
        self.storage = storage
        self.database = database
        self.notifier = notifier

    async def execute(self, event: ImageUploadedEvent) -> ImageProcessedEvent:
        """
        Orchestrates the image digestion process.
        """
        try:
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="PROCESSING_STARTED",
                message="Your image has been picked up by a worker and is now processing.",
                progress=10,
            )

            logger.info(f"Downloading image {event.imageId} from {event.storagePath}")
            raw_image_data = await self.storage.download_image(event.storagePath)
            
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="PROCESSING",
                message="Image downloaded. Starting processing...",
                progress=25,
            )

            logger.info("Starting MediaPipe processing pipeline...")
            processed_bytes, metadata = await self.processor.process_image(
                raw_image_data=raw_image_data, options=event.processingOptions
            )
            
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="PROCESSING",
                message="Processing complete. Uploading results...",
                progress=70,
            )

            logger.info("Uploading processed image to CDN...")
            result_url = await self.storage.upload_image(
                image_id=event.imageId, image_data=processed_bytes
            )

            logger.info("Saving metadata to MongoDB...")
            await self.database.save_image_metadata(
                image_id=event.imageId,
                project_id=event.projectId,
                result_url=result_url,
                metadata=metadata,
            )

            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="PROCESSING_COMPLETED",
                message="Image processing completed successfully!",
                progress=100,
            )

            return ImageProcessedEvent(
                correlationId=event.correlationId,
                imageId=event.imageId,
                projectId=event.projectId,
                userId=event.userId,
                resultUrl=result_url,
                metadata=metadata,
            )

        except Exception as e:
            logger.exception(f"Pipeline failed for image {event.imageId}")
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="PROCESSING_FAILED",
                message=f"An error occurred: {str(e)}",
            )
            raise e
