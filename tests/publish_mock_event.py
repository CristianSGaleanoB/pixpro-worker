import asyncio
import aio_pika
import json
import logging
from uuid import uuid4

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AMQP_URL = "amqp://guest:guest@localhost:5672/"
QUEUE_NAME = "image_upload_events"

async def main():
    connection = await aio_pika.connect_robust(AMQP_URL)
    
    async with connection:
        channel = await connection.channel()
        
        # Declare the queue just in case it doesn't exist yet
        await channel.declare_queue(QUEUE_NAME, durable=True)
        
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
        
        logger.info(f"Publishing mock ImageUploadedEvent to queue '{QUEUE_NAME}'...")
        await channel.default_exchange.publish(
            message,
            routing_key=QUEUE_NAME
        )
        logger.info("Message published successfully.")

if __name__ == "__main__":
    asyncio.run(main())
