from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from src.schemas.base import UserBase


class UserCreateRequest(UserBase):
    """Схема для регистрации пользователя (запрос)"""
    email: str = Field(..., min_length=8, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdateRequest(BaseModel):
    """Схема для обновления пользователя (запрос)"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserLoginRequest(BaseModel):
    """Схема для входа пользователя (запрос)"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)