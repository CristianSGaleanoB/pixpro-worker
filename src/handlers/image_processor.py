import logging
from typing import Type

from src.core.events import ImageUploadedEvent
from src.infrastructure.messaging.base import EventHandlerStrategy
from src.services.digestion_pipeline import DigestionPipeline

logger = logging.getLogger(__name__)

class ImageUploadedHandler(EventHandlerStrategy):
    def __init__(self, pipeline: DigestionPipeline):
        self.pipeline = pipeline

    @property
    def event_type(self) -> Type[ImageUploadedEvent]:
        return ImageUploadedEvent

    async def handle(self, event: ImageUploadedEvent) -> None:
        logger.info(f"Handling ImageUploadedEvent for Image ID: {event.imageId}")
        
        processed_event = await self.pipeline.execute(event)
        
        logger.info("Pipeline execution complete. Resulting event:")
        logger.info(processed_event.model_dump_json(indent=2))

