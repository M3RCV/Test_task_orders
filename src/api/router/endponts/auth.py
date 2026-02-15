from datetime import datetime

from fastapi import Depends, HTTPException, status, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import ValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
)
from src.db.session import get_db
from src.db.dao.users_dao import UserDAO
from src.db.models.user import User
from src.schemas.request.user import UserCreateRequest
from src.schemas.response.user import UserResponse, TokenResponse

router_auth = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"api/v1/auth/token")

limiter = Limiter(key_func=get_remote_address)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
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
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Проверяем активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Получение текущего активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


@router_auth.post("/register", response_model=UserResponse)
@limiter.limit("6/minute")
async def register(
    request: Request,
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Регистрация нового пользователя"""
    user_dao = UserDAO(User, db)

    try:
        # 1. Проверка на существование email
        existing_user = await user_dao.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже зарегистрирован"
            )

        # 2. Хеширование пароля
        hashed_password = get_password_hash(user_data.password)

        # 3. Подготовка данных для создания
        user_dict = {
            "email": user_data.email,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_admin": False,
        }

        # 4. Создание пользователя
        user = await user_dao.create(user_dict)

        # 5. Возвращаем ответ
        return UserResponse.model_validate(user, from_attributes=True)

    except ValidationError as ve:
        # Ошибка валидации Pydantic (например, некорректный email или пароль)
        errors = ve.errors()
        first_error = errors[0]
        field = first_error["loc"][-1]
        msg = first_error["msg"]

        if "email" in field.lower():
            detail = "Incorrect email form"
        elif "password" in field.lower():
            detail = f"week password: {msg}"
        else:
            detail = f"error in data: {msg}"

        raise HTTPException(status_code=422, detail=detail)

    except HTTPException:
        # Пробрасываем HTTP-исключения (например 400 от проверки)
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при регистрации. Попробуйте позже или обратитесь к поддержке."
        )


@router_auth.post("/token", response_model=TokenResponse)
@limiter.limit("6/minute")
async def login_for_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
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
