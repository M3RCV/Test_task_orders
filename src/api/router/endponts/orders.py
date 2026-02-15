from fastapi import APIRouter, Depends, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.api.router.endponts.auth import get_current_active_user
from src.core.kafka import publish_new_order
from src.db.dao.orders_dao import OrderDAO
from src.db.models.order import Order
from src.db.models.user import User
from src.db.redis.redis_utils import get_cached_order, cache_order, invalidate_order_cache
from src.db.redis.session import get_redis
from src.db.session import get_db
from src.schemas.request.order import OrderCreateRequest, OrderStatusUpdate
from src.schemas.response.order import OrderResponse
from uuid import UUID
from fastapi import Request


limiter = Limiter(key_func=get_remote_address)


router_order = APIRouter(
    prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_active_user)]
)


@router_order.post("/", response_model=OrderResponse)
@limiter.limit("10/minute")
async def create_order_endpoint(
    request: Request,
    order_request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """"Эндпоинт для создания заказа"""
    order_dao = OrderDAO(Order, db)

    total_price = 0.0
    for item in order_request.items:
        total_price += item.quantity * item.price

    order_data = order_request.model_dump(exclude_unset=True)
    order_data["items"] = [item.model_dump() for item in order_request.items]

    order_dict = {
        "items": order_data["items"],
        "total_price": total_price,  # ← перезаписываем!
        "status": order_data["status"] or "PENDING",
    }

    order = await order_dao.create(
        order_dict,
        user_id = current_user.id,
    )
    await publish_new_order(str(order.id), current_user.id)
    return OrderResponse.from_orm(order)


@router_order.get("/{order_id}/", response_model=OrderResponse)
@limiter.limit("10/minute")
async def get_order_endpoint(
    request: Request,
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """"Получение заказа по его id"""
    # 1. Пробуем взять из кэша
    cached = await get_cached_order(order_id)

    if cached:
        return OrderResponse(**cached)

    # 2. Нет в кэше → идём в базу
    order_dao = OrderDAO(Order, db)
    db_order = await order_dao.get(id=order_id)

    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 3. Готовим данные для кэширования (убираем служебные поля sqlalchemy)
    order_dict = db_order.__dict__.copy()
    order_dict.pop("_sa_instance_state", None)  # важно!

    # Добавляем поля, которых может не быть в __dict__
    order_dict.setdefault("user_id", db_order.user_id)
    order_dict.setdefault("items", db_order.items)
    order_dict.setdefault("total_price", db_order.total_price)
    order_dict.setdefault("status", db_order.status)
    order_dict.setdefault("created_at", db_order.created_at)

    # 4. Кэшируем через hash
    await cache_order(order_id, order_dict, ttl_seconds=300)

    # 5. Возвращаем из базы
    return db_order


@router_order.patch("/{order_id}/", response_model=OrderResponse)
@limiter.limit("10/minute")
async def update_order_status(
    request: Request,
    order_id: UUID,
    update_data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Обновление статуса заказа (только авторизованные пользователи).
    После обновления инвалидируется кэш.
    """
    order_dao = OrderDAO(Order, db)

    # Получаем заказ из БД
    db_order = await order_dao.get(id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )

    # Проверяем допустимый статус (если не используешь Enum в модели)
    allowed_statuses = {"pending", "paid", "shipped", "canceled"}
    if update_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {', '.join(allowed_statuses)}"
        )

    # Обновляем в базе
    updated_order = await order_dao.update(
        id=order_id,
        obj_in={"status": update_data.status}
    )

    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while updating status"
        )

    # Инвалидируем кэш
    await invalidate_order_cache(order_id)

    return updated_order


@router_order.get("/user/{user_id}/", response_model=list[OrderResponse])
@limiter.limit("10/minute")
async def get_user_orders(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Получение списка заказов конкретного пользователя.
    Рекомендуется проверять, что запрашивает свои заказы или админ.
    """

    order_dao = OrderDAO(Order, db)

    orders = await order_dao.get_user_orders(user_id=user_id)

    if not orders:
        return []

    orders_sorted = sorted(orders, key=lambda o: o.created_at, reverse=True)

    return orders_sorted