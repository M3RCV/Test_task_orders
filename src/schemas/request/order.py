from pydantic import BaseModel, Field, computed_field
from typing import Optional, List

from src.schemas.base import OrderBase, OrderStatus, OrderItemBase


class OrderStatusUpdate(BaseModel):
    """Схема для обновления статуса заказа (запрос)"""

    status: OrderStatus = Field(..., description="Новый статус заказа")


class OrderItemCreateRequest(OrderItemBase):
    """Схема товара для создания заказа (запрос)"""

    pass


class OrderUpdateRequest(BaseModel):
    """Схема для обновления статуса заказа (запрос)"""

    status: Optional[OrderStatus] = None


class OrderItem(OrderItemBase):
    """Схема товара в ответе API"""

    @computed_field
    @property
    def total(self) -> float:
        return self.quantity * self.price


class OrderCreateRequest(OrderBase):
    """Схема для создания заказа (запрос)"""

    items: List[OrderItem]
    pass
