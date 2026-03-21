from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
)
from src.db.dao.users_dao import UserDAO
from src.db.models.user import User
from src.schemas.request.user import UserCreateRequest


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_dao = UserDAO(User, db)

    async def register_user(self, user_data: UserCreateRequest) -> User:
        existing_user = await self.user_dao.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                400,
                detail="User with this email currently registrated",
            )

        hashed_password = get_password_hash(user_data.password)

        user_dict = {
            "email": user_data.email,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_admin": False,
        }

        return await self.user_dao.create(user_dict)

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_dao.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    def create_token(self, user: User) -> str:
        return create_access_token(data={"sub": user.email})

    async def get_current_user(self, token: str) -> User:
        payload = decode_token(token)

        if not payload:
            raise HTTPException(
                401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email = payload.get("sub")
        if not email:
            raise HTTPException(
                401,
                detail="Invalid token payload",
            )

        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                401,
                detail="Token has expired",
            )

        user = await self.user_dao.get_by_email(email)

        if not user:
            raise HTTPException(
                404,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                400,
                detail="Inactive user",
            )

        return user
