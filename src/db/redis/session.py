import logging
from typing import Optional
from redis.asyncio import Redis, from_url
from src.core.config import settings  # предполагается, что там есть REDIS_URL

logger = logging.getLogger(__name__)

# Глобальный клиент (инициализируется один раз)
_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Получить или создать асинхронное подключение к Redis
    """
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = await from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Проверка подключения
            await _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error("Failed to connect to Redis", exc_info=True)
            raise
    return _redis_client


async def close_redis():
    """Закрыть соединение при завершении приложения"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")