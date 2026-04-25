from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

class BaseEvent(BaseModel):
    event: str
    version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlationId: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ProcessingOptions(BaseModel):
    upscaler: bool
    grayscale: bool
    restore: bool
    watermark: Optional[str] = None

class ImageUploadedEvent(BaseEvent):
    event: str = Field(default="ImageUploaded", frozen=True)
    projectId: str
    userId: str
    imageId: str
    storagePath: str
    processingOptions: ProcessingOptions

class ProcessingMetadata(BaseModel):
    processedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    durationMs: int
    appliedOptions: List[str]

class ImageProcessedEvent(BaseEvent):
    event: str = Field(default="ImageProcessed", frozen=True)
    imageId: str
    projectId: str
    userId: str
    resultUrl: str
    metadata: ProcessingMetadata
