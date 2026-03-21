from pydantic import BaseModel, ConfigDict, computed_field
from typing import List

from src.schemas.base import OrderInDB, OrderItemBase, OrderBase


class OrderResponse(OrderInDB):
    """Схема заказа в ответе API"""

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def items_count(self) -> int:
        return len(self.items) if self.items else 0


class OrderListResponse(BaseModel):
    """Схема списка заказов в ответе API"""

    orders: List[OrderResponse]
    total: int
    page: int
    size: int
