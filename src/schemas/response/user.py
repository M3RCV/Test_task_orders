from pydantic import BaseModel
from datetime import datetime

from src.schemas.base import UserInDB


class UserResponse(UserInDB):
    """Схема пользователя в ответе API"""
    pass


class TokenResponse(BaseModel):
    """Схема JWT токена в ответе"""
    access_token: str
    token_type: str = "bearer"


class UserWithTokenResponse(BaseModel):
    """Схема пользователя с токеном"""
    user: UserResponse
    token: TokenResponse