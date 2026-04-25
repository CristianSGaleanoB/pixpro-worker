import pytest
from src.core.events import ImageUploadedEvent, ProcessingOptions
from src.handlers.image_processor import ImageUploadedHandler

from src.services.digestion_pipeline import DigestionPipeline
from src.core.processor import MediaPipeProcessorMock
from src.infrastructure.storage.cdn import CDNStorageMock
from src.infrastructure.database.mongo import MongoDBRepositoryMock
from src.infrastructure.notifications.websocket import WebSocketNotifierMock

async def test_image_uploaded_handler_processes_event(caplog):
    import logging
    caplog.set_level(logging.INFO)
    
    # Prepare mock input
    options = ProcessingOptions(
        upscaler=True,
        grayscale=False,
        restore=True,
        watermark="Confidential"
    )
    
    event = ImageUploadedEvent(
        projectId="project-123",
        userId="user-456",
        imageId="image-789",
        storagePath="s3://raw-bucket/project-123/image-789.jpg",
        processingOptions=options
    )
    
    # Instantiate mocks and pipeline
    pipeline = DigestionPipeline(
        processor=MediaPipeProcessorMock(),
        storage=CDNStorageMock(),
        database=MongoDBRepositoryMock(),
        notifier=WebSocketNotifierMock()
    )
    
    # Run the handler
    handler = ImageUploadedHandler(pipeline=pipeline)
    await handler.handle(event)
    
    # Assert logs contain the expected output from the pipeline execution
    assert "Handling ImageUploadedEvent for Image ID: image-789" in caplog.text
    assert "Downloading image image-789" in caplog.text
    assert "Applying AI upscaling... (mock)" in caplog.text
    assert "Simulating CDN upload for image-789" in caplog.text
    assert "Successfully saved metadata to MongoDB" in caplog.text
    assert "Simulating WebSocket emit to user user-456: [Image image-789] Status: PROCESSING_COMPLETED" in caplog.text
