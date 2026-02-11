from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

from src.schemas.base import OrderInDB, OrderStatus, OrderItemBase


class OrderItemResponse(OrderItemBase):
    """Схема товара в ответе API"""
    total: float = Field(..., gt=0)

    @property
    def total(self) -> float:
        return self.quantity * self.price


class OrderResponse(OrderInDB):
    """Схема заказа в ответе API"""
    items_count: int

    model_config = ConfigDict(from_attributes=True)

    @property
    def items_count(self) -> int:
        return len(self.items) if self.items else 0


class OrderListResponse(BaseModel):
    """Схема списка заказов в ответе API"""
    orders: List[OrderResponse]
    total: int
    page: int
    size: int