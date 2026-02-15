from pydantic import BaseModel, Field, ConfigDict, validator, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from enum import Enum


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False


class UserInDB(UserBase):
    """Схема пользователя в базе данных"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatus(str, Enum):
    """Статусы заказа"""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELED = "canceled"


class OrderItemBase(BaseModel):
    """Базовая схема товара в заказе"""
    product_id: str
    name: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v


class OrderBase(BaseModel):
    """Базовая схема заказа"""
    items: List[Dict[str, Any]] = Field(default_factory=list)

    status: OrderStatus = OrderStatus.PENDING

    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Order must contain at least one item')
        return v

class OrderInDB(OrderBase):
    """Схема заказа в базе данных"""
    total_price: float = Field(gt=0)
    id: uuid.UUID
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)