import logging
import aio_pika
from aio_pika.abc import (
    AbstractRobustConnection,
    AbstractChannel,
    AbstractExchange,
    ExchangeType,
)
from typing import Optional

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    def __init__(
        self,
        amqp_url: str,
        exchange: str,
        exchange_type: str = "topic",
    ):
        self.amqp_url = amqp_url
        self.exchange_name = exchange
        self.exchange_type = exchange_type
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange_obj: Optional[AbstractExchange] = None

    async def connect(self) -> None:
        if not self.connection or self.connection.is_closed:
            logger.info(f"Connecting to RabbitMQ at {self.amqp_url}")
            self.connection = await aio_pika.connect_robust(self.amqp_url)
            self.channel = await self.connection.channel()

            self.exchange_obj = await self.channel.declare_exchange(
                self.exchange_name,
                ExchangeType(self.exchange_type),
                durable=True,
            )
            logger.info(
                f'Exchange declared: "{self.exchange_name}" ({self.exchange_type})'
            )
            logger.info("Successfully connected to RabbitMQ")

    async def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            logger.info("Closing RabbitMQ connection")
            await self.connection.close()
