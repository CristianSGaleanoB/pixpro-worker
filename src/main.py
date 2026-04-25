import asyncio
import logging
import sys

from src.infrastructure.rabbitmq.connection import RabbitMQConnection
from src.infrastructure.rabbitmq.consumer import RabbitMQConsumer
from src.handlers.image_processor import ImageUploadedHandler

# Import new pipeline and mocks
from src.services.digestion_pipeline import DigestionPipeline
from src.core.processor import MediaPipeProcessorMock
from src.infrastructure.storage.cdn import CDNStorageMock
from src.infrastructure.database.mongo import MongoDBRepositoryMock
from src.infrastructure.notifications.websocket import WebSocketNotifierMock
from src.core.config import settings

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Digester Worker")
    
    # 1. Establish RabbitMQ Connection
    connection = RabbitMQConnection(amqp_url=settings.amqp_url)
    await connection.connect()

    # 2. Instantiate infrastructure mocks
    processor = MediaPipeProcessorMock()
    storage = CDNStorageMock()
    database = MongoDBRepositoryMock()
    notifier = WebSocketNotifierMock()

    # 3. Instantiate pipeline
    pipeline = DigestionPipeline(
        processor=processor,
        storage=storage,
        database=database,
        notifier=notifier
    )

    # 4. Instantiate strategy (handler)
    handler = ImageUploadedHandler(pipeline=pipeline)

    # 5. Create consumer and inject dependencies
    consumer = RabbitMQConsumer(
        connection=connection,
        queue_name=settings.queue_name,
        strategy=handler
    )

    try:
        # 6. Start listening
        await consumer.start_consuming()
    except asyncio.CancelledError:
        pass
    finally:
        await connection.close()
        logger.info("Worker stopped.")

def run():
    """Entry point for the CLI script defined in pyproject.toml"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting.")

if __name__ == "__main__":
    run()
