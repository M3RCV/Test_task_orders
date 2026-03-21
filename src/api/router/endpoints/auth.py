from fastapi import Depends, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models.user import User
from src.schemas.request.user import UserCreateRequest
from src.schemas.response.user import UserResponse, TokenResponse
from src.services.auth_service import AuthService

router_auth = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"api/v1/auth/token")

limiter = Limiter(key_func=get_remote_address)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    service = AuthService(db)
    return await service.get_current_user(token)


@router_auth.post("/register", response_model=UserResponse)
@limiter.limit("6/minute")
async def register(
    request: Request,
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)

    user = await service.register_user(user_data)

    return UserResponse.model_validate(user, from_attributes=True)


@router_auth.post("/token", response_model=TokenResponse)
@limiter.limit("6/minute")
async def login_for_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)

    user = await service.authenticate_user(form_data.username, form_data.password)

    access_token = service.create_token(user)

    return TokenResponse(access_token=access_token, token_type="bearer")
