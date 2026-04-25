import asyncio
import logging
from src.core.interfaces import DatabaseRepository
from src.core.events import ProcessingMetadata

logger = logging.getLogger(__name__)

class MongoDBRepositoryMock(DatabaseRepository):
    async def save_image_metadata(self, image_id: str, project_id: str, result_url: str, metadata: ProcessingMetadata) -> None:
        logger.info(f"Simulating MongoDB insert for image {image_id} (Project: {project_id})...")
        await asyncio.sleep(0.1)
        # E.g. db.images.update_one({'_id': image_id}, {'$set': {'status': 'done', 'url': result_url, ...}})
        logger.info("Successfully saved metadata to MongoDB.")
