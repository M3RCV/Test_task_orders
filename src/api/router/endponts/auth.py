from datetime import datetime

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash, verify_password, create_access_token, decode_token
from src.db.session import get_db
from src.db.dao.users_dao import UserDAO
from src.db.models.user import User
from src.schemas.request.user import UserCreateRequest
from src.schemas.response.user import UserResponse, TokenResponse

router_auth = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"api/v1/auth/token")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    """Получение текущего пользователя из JWT токена"""

    # Декодируем токен
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем наличие email
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Проверяем истечение токена
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )

    # Ищем пользователя
    user_dao = UserDAO(User, db)
    user = await user_dao.get_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Проверяем активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Получение текущего активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


@router_auth.post("/register", response_model=UserResponse)
async def register(user_data: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    user_dao = UserDAO(User, db)

    # Проверяем существует ли email
    existing_user = await user_dao.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Хешируем пароль
    hashed_password = get_password_hash(user_data.password)

    # Создаем пользователя
    user_dict = {
        "email": user_data.email,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_admin": False,
    }

    user = await user_dao.create(user_dict)
    return UserResponse.from_orm(user)


@router_auth.post("/token", response_model=TokenResponse)
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Эндпоинт для OAuth2 (используется Swagger UI)"""
    user_dao = UserDAO(User, db)

    # username в OAuth2 = email
    user = await user_dao.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создаем токен
    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router_auth.get("/me")
async def read_current_user(current_user: User = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
    }
