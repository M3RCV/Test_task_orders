from pydantic import BaseModel, Field
from typing import Optional, List

from src.schemas.base import OrderBase, OrderStatus, OrderItemBase
from src.schemas.response.order import OrderItemResponse


class OrderStatusUpdate(BaseModel):
    """Схема для обновления статуса заказа (запрос)"""
    status: OrderStatus = Field(
        ...,
        description="Новый статус заказа"
    )


class OrderItemCreateRequest(OrderItemBase):
    """Схема товара для создания заказа (запрос)"""
    pass


class OrderCreateRequest(OrderBase):
    """Схема для создания заказа (запрос)"""
    items: List[OrderItemResponse]
    pass


class OrderUpdateRequest(BaseModel):
    """Схема для обновления статуса заказа (запрос)"""
    status: Optional[OrderStatus] = None