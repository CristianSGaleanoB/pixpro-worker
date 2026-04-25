import logging
import aio_pika
from typing import Optional

logger = logging.getLogger(__name__)

class RabbitMQConnection:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None

    async def connect(self) -> None:
        """Establishes connection and channel to RabbitMQ."""
        if not self.connection or self.connection.is_closed:
            logger.info(f"Connecting to RabbitMQ at {self.amqp_url}")
            self.connection = await aio_pika.connect_robust(self.amqp_url)
            self.channel = await self.connection.channel()
            logger.info("Successfully connected to RabbitMQ")

    async def close(self) -> None:
        """Closes the connection safely."""
        if self.connection and not self.connection.is_closed:
            logger.info("Closing RabbitMQ connection")
            await self.connection.close()
