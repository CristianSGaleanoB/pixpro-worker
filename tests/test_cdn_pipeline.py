import pytest
from unittest.mock import AsyncMock
from src.services.digestion_pipeline import DigestionPipeline
from src.core.events import ImageUploadedEvent, ProcessingOptions
from tests.support.mocks import CDNStorageMock, WebSocketNotifierMock


@pytest.fixture
def mock_event():
    return ImageUploadedEvent(
        event="ImageUploaded",
        version="1.0",
        timestamp="2026-05-08T00:00:00Z",
        correlationId="corr-123",
        projectId="proj-456",
        userId="user-789",
        imageId="img-abc",
        storagePath="https://res.cloudinary.com/mock/raw/proj-456/img-abc.png",
        processingOptions=ProcessingOptions(
            upscaler=True,
            grayscale=False,
            restore=True,
            watermark="PixPro",
        ),
    )


@pytest.fixture
def pipeline():
    # Mock Processor that simulates processing without real AI logic, returning dummy
    # processed data and metadata
    processor_mock = AsyncMock()
    from src.core.events import ProcessingMetadata
    from datetime import datetime, timezone

    processor_mock.process_image.return_value = (
        b"processed-image-data",
        ProcessingMetadata(
            processedAt=datetime.now(timezone.utc).isoformat(),
            durationMs=2000,
            appliedOptions=["upscaler", "restore"],
        ),
    )

    return DigestionPipeline(
        processor=processor_mock,
        storage=CDNStorageMock(),
        database=AsyncMock(),
        notifier=WebSocketNotifierMock(),
    )


@pytest.mark.asyncio
async def test_pipeline_calls_cdn_download(pipeline, mock_event):
    """The pipeline must download the image from the storagePath from the event."""
    await pipeline.execute(mock_event)

    assert mock_event.storagePath in pipeline.storage.downloaded


@pytest.mark.asyncio
async def test_pipeline_calls_cdn_upload(pipeline, mock_event):
    """The pipeline must upload the processed image to the CDN exactly once."""
    await pipeline.execute(mock_event)

    assert len(pipeline.storage.uploaded) == 1
    assert pipeline.storage.uploaded[0]["image_id"] == mock_event.imageId


@pytest.mark.asyncio
async def test_pipeline_result_url_comes_from_cdn(pipeline, mock_event):
    """The resultUrl of the ImageProcessed event must come from the CDN, not be hardcoded."""
    result = await pipeline.execute(mock_event)

    assert result.resultUrl.startswith("https://res.cloudinary.com/mock/")
    assert mock_event.imageId in result.resultUrl


@pytest.mark.asyncio
async def test_pipeline_notifies_complete_status(pipeline, mock_event):
    """Upon successful completion, the pipeline must notify status=complete progress=100."""
    notifications = []
    original_notify = pipeline.notifier.notify_status

    async def capturing_notify(**kwargs):
        notifications.append(kwargs)
        await original_notify(**kwargs)

    pipeline.notifier.notify_status = capturing_notify

    await pipeline.execute(mock_event)

    last = notifications[-1]
    assert last["status"] == "complete"
    assert last["progress"] == 100
