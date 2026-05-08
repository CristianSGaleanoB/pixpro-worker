import asyncio
import logging
import sys

from src.infrastructure.rabbitmq.connection import RabbitMQConnection
from src.infrastructure.rabbitmq.consumer import RabbitMQConsumer
from src.handlers.image_processor import ImageUploadedHandler
from src.services.digestion_pipeline import DigestionPipeline
from src.core.processor import MediaPipeProcessorMock
from src.infrastructure.storage.cdn import CloudinaryCDNStorage
from src.infrastructure.database.mongo import MongoDBRepositoryMock
from src.infrastructure.notifications.websocket import SocketIONotifier
from src.core.config import settings
from src.infrastructure.storage.cdn import CloudinaryCDNStorage


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting Digester Worker")

    # Infrastructure
    connection = RabbitMQConnection(
        amqp_url=settings.amqp_url,
        exchange=settings.exchange,
        exchange_type=settings.exchange_type,
    )
    await connection.connect()

    notifier = SocketIONotifier()
    await notifier.start()

    processor = MediaPipeProcessorMock()
    storage = CloudinaryCDNStorage()
    database = MongoDBRepositoryMock()

    # Domain pipeline
    pipeline = DigestionPipeline(
        processor=processor,
        storage=storage,
        database=database,
        notifier=notifier,
    )

    handler = ImageUploadedHandler(pipeline=pipeline)

    consumer = RabbitMQConsumer(
        connection=connection,
        queue_name=settings.queue_name,
        routing_key=settings.routing_key,
        strategy=handler,
    )

    try:
        await consumer.start_consuming()
    except asyncio.CancelledError:
        pass
    finally:
        await notifier.stop()
        await connection.close()
        logger.info("Worker stopped.")


def run():
    """Entry point for the CLI script defined in pyproject.toml."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting.")


if __name__ == "__main__":
    run()
