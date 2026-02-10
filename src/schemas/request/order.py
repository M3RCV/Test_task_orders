from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from src.schemas.base import OrderBase, OrderStatus, OrderItemBase


class OrderItemCreateRequest(OrderItemBase):
    """Схема товара для создания заказа (запрос)"""
    pass


class OrderCreateRequest(OrderBase):
    """Схема для создания заказа (запрос)"""
    pass


class OrderUpdateRequest(BaseModel):
    """Схема для обновления статуса заказа (запрос)"""
    status: Optional[OrderStatus] = None