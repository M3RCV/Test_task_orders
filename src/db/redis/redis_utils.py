import json
import logging
from typing import Optional, Dict, Any
from uuid import UUID

from src.db.redis.session import get_redis


logger = logging.getLogger(__name__)

async def cache_order(order_id: str | UUID, order_data: dict, ttl_seconds: int = 300) -> None:
    """
    Сохраняет заказ в Redis как hash.
    order_id может быть str или UUID.
    """
    redis = await get_redis()
    order_id_str = str(order_id)

    # Подготавливаем данные для хранения
    data_to_cache = {
        "user_id": str(order_data.get("user_id", 0)),
        "items": json.dumps(order_data.get("items", [])),
        "total_price": str(order_data.get("total_price", 0.0)),
        "status": order_data.get("status", "PENDING"),
        "created_at": str(order_data.get("created_at", "")),
    }

    key = f"order:{order_id_str}"

    try:
        await redis.hset(key, mapping=data_to_cache)
        await redis.expire(key, ttl_seconds)
        logger.debug(f"Order {order_id_str} cached (hash) with TTL {ttl_seconds}s")
    except Exception as e:
        logger.error(f"Failed to cache order {order_id_str}", exc_info=True)


async def get_cached_order(order_id: str | UUID) -> Optional[Dict[str, Any]]:
    """
    Получает заказ из Redis hash.
    order_id может быть str или UUID.
    Возвращает восстановленный словарь или None.
    """
    redis = await get_redis()
    order_id_str = str(order_id)
    key = f"order:{order_id_str}"

    try:
        data = await redis.hgetall(key)
        if not data:
            return None

        # Восстанавливаем типы
        restored = {
            "order_id": order_id_str,
            "user_id": int(data.get("user_id", "0")),
            "items": json.loads(data.get("items", "[]")),
            "total_price": float(data.get("total_price", "0.0")),
            "status": data.get("status", "PENDING"),
            "created_at": data.get("created_at", ""),
        }
        return restored

    except Exception as e:
        logger.error(f"Error getting cached order {order_id_str}", exc_info=True)
        return None


async def invalidate_order_cache(order_id: str | UUID):
    """Удалить заказ из кэша (например, после обновления статуса)"""
    redis = await get_redis()
    key = f"order:{order_id}"
    deleted = await redis.delete(key)
    if deleted:
        logger.debug(f"Cache invalidated for order {order_id}")
    else:
        logger.debug(f"No cache to invalidate for order {order_id}")