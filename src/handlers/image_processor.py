import logging
from typing import TYPE_CHECKING

from src.core.events import ImageUploadedEvent
from src.infrastructure.messaging.base import EventHandlerStrategy
from src.services.digestion_pipeline import DigestionPipeline
from src.core.correlation_logger import CorrelationLogger

if TYPE_CHECKING:
    from typing import Type

logger = CorrelationLogger(__name__)


class ImageUploadedHandler(EventHandlerStrategy[ImageUploadedEvent]):
    def __init__(self, pipeline: DigestionPipeline):
        self.pipeline = pipeline

    @property
    def event_type(self) -> "Type[ImageUploadedEvent]":
        return ImageUploadedEvent

    async def handle(self, event: ImageUploadedEvent) -> None:
        cid = event.correlationId
        logger.info(f"Handling ImageUploadedEvent for Image ID: {event.imageId}", cid)

        processed_event = await self.pipeline.execute(event)

        logger.info("Pipeline execution complete", cid)
