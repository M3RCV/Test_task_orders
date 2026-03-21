from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.router.endpoints.auth import get_current_user
from src.db.models.user import User
from src.db.redis.session import get_redis
from src.db.session import get_db
from src.schemas.request.order import OrderStatusUpdate, OrderCreateRequest
from src.schemas.response.order import OrderResponse
from uuid import UUID
from fastapi import Request

from src.services.order_service import OrderService

limiter = Limiter(key_func=get_remote_address)


router_order = APIRouter(
    prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_user)]
)


@router_order.post("/", response_model=OrderResponse)
@limiter.limit("10/minute")
async def create_order_endpoint(
    request: Request,
    order_request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ "Эндпоинт для создания заказа"""
    order_service = OrderService(db, current_user)

    order = await order_service.create_new_order(order_request)

    return OrderResponse.from_orm(order)


@router_order.get("/{order_id}/", response_model=OrderResponse)
@limiter.limit("10/minute")
async def get_order_endpoint(
    request: Request,
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    """Получение заказа по его id"""
    order_service = OrderService(db, current_user)
    order = await order_service.get_order_by_id(db, order_id=order_id)
    return order


@router_order.patch("/{order_id}/", response_model=OrderResponse)
@limiter.limit("10/minute")
async def update_order_status_endpoint(
    request: Request,
    order_id: UUID,
    update_data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    """
    Обновление статуса заказа (только авторизованные пользователи).
    После обновления инвалидируется кэш.
    """
    order_service = OrderService(db, current_user)
    updated_order = await order_service.update_order_status(
        order_id, update_data, current_user.id
    )
    return updated_order


@router_order.get("/user/{user_id}/", response_model=list[OrderResponse])
@limiter.limit("10/minute")
async def get_user_orders_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение списка заказов текущего пользователя
    """

    order_service = OrderService(db, current_user)
    orders_sorted = await order_service.get_user_orders()
    return orders_sorted
