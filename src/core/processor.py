import asyncio
import logging
from src.core.interfaces import ImageProcessingService
from src.core.events import ProcessingOptions, ProcessingMetadata

logger = logging.getLogger(__name__)


class MediaPipeProcessorMock(ImageProcessingService):
    async def process_image(
        self, raw_image_data: bytes, options: ProcessingOptions
    ) -> tuple[bytes, ProcessingMetadata]:
        logger.info("Initializing MediaPipe models... (mock)")
        await asyncio.sleep(0.5)  # Simulate model load

        applied = []
        if options.upscaler:
            logger.info("Applying AI upscaling... (mock)")
            await asyncio.sleep(1)
            applied.append("upscaler")

        if options.grayscale:
            logger.info("Applying grayscale filter... (mock)")
            await asyncio.sleep(0.2)
            applied.append("grayscale")

        if options.restore:
            logger.info("Restoring facial features... (mock)")
            await asyncio.sleep(1)
            applied.append("restore")

        if options.watermark:
            logger.info(f"Adding watermark '{options.watermark}'... (mock)")
            await asyncio.sleep(0.3)
            applied.append(f"watermark:{options.watermark}")

        metadata = ProcessingMetadata(durationMs=2000, appliedOptions=applied)

        processed_bytes = b"MOCK_PROCESSED_IMAGE_BYTES"

        return processed_bytes, metadata
