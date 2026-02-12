import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer

from src.core.config import settings
from src.tasks.celery_task import process_order

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def consume():
    consumer = AIOKafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        auto_offset_reset="latest",  # для тестов удобно latest
        enable_auto_commit=True,
    )

    await consumer.start()
    log.info(f"Consumer started, listening topic {settings.kafka_topic}")

    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode("utf-8"))
                order_id = data["order_id"]

                log.info(f"Received new_order event for order {order_id}")

                # Кидаем задачу в Celery
                process_order.delay(order_id)

            except Exception as e:
                log.exception(f"Error processing message: {e}")
                # не падаем — продолжаем читать очередь
    finally:
        await consumer.stop()
        log.info("Consumer stopped")


if __name__ == "__main__":
    asyncio.run(consume())
