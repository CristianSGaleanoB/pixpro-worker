import asyncio
import aio_pika
import json
import logging
from src.core.config import settings
from uuid import uuid4

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    connection = await aio_pika.connect_robust(settings.amqp_url)
    
    async with connection:
        channel = await connection.channel()
        
        # Declare the queue just in case it doesn't exist yet
        await channel.declare_queue(settings.queue_name, durable=True)
        
        # Build the payload matching our Pydantic model
        payload = {
            "event": "ImageUploaded",
            "version": "1.0",
            "correlationId": str(uuid4()),
            "projectId": "proj-999",
            "userId": "usr-888",
            "imageId": "img-777",
            "storagePath": "s3://some-bucket/img-777.png",
            "processingOptions": {
                "upscaler": True,
                "grayscale": False,
                "restore": True,
                "watermark": "MyWatermark"
            }
        }
        
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        logger.info(f"Publishing mock ImageUploadedEvent to queue '{settings.queue_name}'...")
        await channel.default_exchange.publish(
            message,
            routing_key=settings.queue_name
        )
        logger.info("Message published successfully.")

if __name__ == "__main__":
    asyncio.run(main())
