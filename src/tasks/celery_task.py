from celery import Celery
import time

from src.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

@celery_app.task(name="process_order")
def process_order(order_id: str):
    time.sleep(2)
    print(f"Order {order_id} processed")  # как просили в ТЗ
    # здесь можно обновить статус в БД и инвалидировать кэш