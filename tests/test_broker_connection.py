import pytest
import asyncio
from src.infrastructure.rabbitmq.connection import RabbitMQConnection
from src.core.config import settings
import aio_pika

@pytest.mark.asyncio
async def test_rabbitmq_connection_success():
    connection = RabbitMQConnection(amqp_url=settings.amqp_url)
    try:
        await asyncio.wait_for(connection.connect(), timeout=5.0)
        
        assert connection.connection is not None
        assert not connection.connection.is_closed
        assert connection.channel is not None
        assert not connection.channel.is_closed
        
    except (aio_pika.exceptions.AMQPConnectionError, asyncio.TimeoutError, ConnectionError) as e:
        pytest.fail(f"Could not connect to RabbitMQ broker at {settings.amqp_url}. Ensure it is running. Error: {e}")
    finally:
        await connection.close()
