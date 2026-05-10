import pytest
import logging
from src.core.events import ImageUploadedEvent, ProcessingOptions
from src.handlers.image_processor import ImageUploadedHandler

from src.services.digestion_pipeline import DigestionPipeline
from src.core.processor import MediaPipeProcessorMock
from src.infrastructure.storage.cdn import CloudinaryCDNStorage
from src.infrastructure.database.mongo import MongoDBRepositoryMock
from tests.support.mocks import WebSocketNotifierMock, CDNStorageMock


async def test_image_uploaded_handler_processes_event(caplog):
    caplog.set_level(logging.INFO)

    options = ProcessingOptions(
        upscaler=True, grayscale=False, restore=True, watermark="Confidential"
    )

    event = ImageUploadedEvent(
        projectId="project-123",
        userId="user-456",
        imageId="image-789",
        storagePath="https://res.cloudinary.com/mock/raw/project-123/image-789.jpg",
        processingOptions=options,
    )

    pipeline = DigestionPipeline(
        processor=MediaPipeProcessorMock(),
        storage=CDNStorageMock(),
        database=MongoDBRepositoryMock(),
        notifier=WebSocketNotifierMock(),
    )

    handler = ImageUploadedHandler(pipeline=pipeline)
    await handler.handle(event)

    assert "Handling ImageUploadedEvent for Image ID: image-789" in caplog.text
    assert "Downloading image image-789" in caplog.text
    assert "Applying AI upscaling... (mock)" in caplog.text
