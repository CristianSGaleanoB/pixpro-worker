import logging
from src.core.events import ImageUploadedEvent, ImageProcessedEvent
from src.core.interfaces import (
    ImageProcessingService,
    StorageService,
    DatabaseRepository,
    NotificationService,
)
from src.core.retry_utils import retry_with_backoff
from src.core.circuit_breaker import CircuitBreaker
from src.core.correlation_logger import CorrelationLogger

logger = CorrelationLogger(__name__)


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
        self.cdn_circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
        self.cdn_circuit._name = "CDN Circuit"
        self.db_circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        self.db_circuit._name = "MongoDB Circuit"

    async def execute(self, event: ImageUploadedEvent) -> ImageProcessedEvent:
        cid = event.correlationId
        try:
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="processing",
                progress=0,
                message="Your image has been picked up by a worker.",
            )

            logger.info(f"Downloading image {event.imageId} from {event.storagePath}", cid)
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="processing",
                progress=10,
                message="Downloading image from storage...",
            )
            raw_image_data = await retry_with_backoff(
                self.cdn_circuit.call,
                self.storage.download_image,
                event.storagePath,
                max_retries=3,
            )

            logger.info("Starting MediaPipe processing pipeline...", cid)
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="processing",
                progress=50,
                message="Applying AI enhancements...",
            )
            processed_bytes, metadata = await self.processor.process_image(
                raw_image_data=raw_image_data, options=event.processingOptions
            )

            logger.info("Uploading processed image to CDN...", cid)
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="processing",
                progress=75,
                message="Uploading processed image...",
            )
            result_url = await retry_with_backoff(
                self.cdn_circuit.call,
                self.storage.upload_image,
                image_id=event.imageId,
                image_data=processed_bytes,
                max_retries=3,
            )

            logger.info("Saving metadata to MongoDB...", cid)
            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="processing",
                progress=90,
                message="Saving metadata...",
            )
            await retry_with_backoff(
                self.db_circuit.call,
                self.database.save_image_metadata,
                image_id=event.imageId,
                project_id=event.projectId,
                result_url=result_url,
                metadata=metadata,
                max_retries=3,
            )

            await self.notifier.notify_status(
                user_id=event.userId,
                image_id=event.imageId,
                status="complete",
                progress=100,
                message="Image processing completed successfully!",
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
            if "is OPEN" in str(e):
                logger.error(f"Circuit breaker open: {e}", cid)
                await self.notifier.notify_status(
                    user_id=event.userId,
                    image_id=event.imageId,
                    status="failed",
                    progress=0,
                    message="Service temporarily unavailable. Please try again later.",
                )
            else:
                logger.exception(f"Pipeline failed for image {event.imageId}", cid)
                await self.notifier.notify_status(
                    user_id=event.userId,
                    image_id=event.imageId,
                    status="failed",
                    progress=0,
                    message=f"An error occurred: {str(e)}",
                )
            raise e
