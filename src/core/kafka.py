from aiokafka import AIOKafkaProducer
from contextlib import asynccontextmanager
import json
import logging

from src.core.config import settings


log = logging.getLogger(__name__)

# Глобальная переменная (будет создана один раз)
_producer: AIOKafkaProducer | None = None

async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,  # в docker-compose сервис kafka
            acks=1,                     # достаточно для тестового
            compression_type="gzip",
        )
        await _producer.start()
        log.info("Kafka producer started")
    return _producer


@asynccontextmanager
async def lifespan_producer(app):
    # startup
    await get_producer()
    yield
    # shutdown
    global _producer
    if _producer:
        await _producer.stop()
        log.info("Kafka producer stopped")


async def publish_new_order(order_id: str, user_id: int):
    producer = await get_producer()
    data = {
        "event": "new_order",
        "order_id": order_id,
        "user_id": user_id,
    }
    value = json.dumps(data).encode("utf-8")

    await producer.send_and_wait(
        topic=settings.kafka_topic,
        value=value,
    )
    log.info(f"Published new_order event for order {order_id}")