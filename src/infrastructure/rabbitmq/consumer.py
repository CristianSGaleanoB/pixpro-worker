import json
import logging
import asyncio
from aio_pika.abc import AbstractIncomingMessage
from pydantic import ValidationError

from src.infrastructure.messaging.base import EventHandlerStrategy
from src.infrastructure.rabbitmq.connection import RabbitMQConnection

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self, connection: RabbitMQConnection, queue_name: str, strategy: EventHandlerStrategy):
        self.connection = connection
        self.queue_name = queue_name
        self.strategy = strategy

    async def _process_message(self, message: AbstractIncomingMessage) -> None:
        async with message.process(ignore_processed=True):
            try:
                # Decode body
                body = message.body.decode()
                payload = json.loads(body)
                
                # Parse using the strategy's expected Pydantic model
                event_model = self.strategy.event_type(**payload)
                
                # Delegate to the strategy
                logger.info(f"Received valid event: {event_model.event} (Correlation ID: {event_model.correlationId})")
                await self.strategy.handle(event_model)
                
                # Acknowledge message manually if all goes well
                await message.ack()

            except json.JSONDecodeError:
                logger.error("Failed to decode message body as JSON. Rejecting message.")
                await message.reject(requeue=False)
            except ValidationError as e:
                logger.error(f"Message payload failed validation: {e.errors()}. Rejecting message.")
                await message.reject(requeue=False)
            except Exception as e:
                logger.exception(f"Unexpected error processing message: {e}")
                # Requeue on unexpected error for retry mechanism (could be customized)
                await message.nack(requeue=True)

    async def start_consuming(self) -> None:
        """Starts consuming from the queue using the provided strategy."""
        if not self.connection.channel:
            raise RuntimeError("RabbitMQ connection is not established. Call connect() first.")
        
        # Declare queue
        queue = await self.connection.channel.declare_queue(self.queue_name, durable=True)
        
        logger.info(f"Started consuming from queue '{self.queue_name}'")
        await queue.consume(self._process_message)
        
        # Keep consumer running
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            logger.info("Consumer stopped.")
