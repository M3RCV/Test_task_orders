from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dao.orders_dao import OrderDAO
from src.db.models.order import Order
from src.db.models.user import User
from src.db.redis.redis_utils import get_or_set, invalidate_order_cache
from src.schemas.request.order import OrderStatusUpdate, OrderCreateRequest
from src.schemas.response.order import OrderResponse


def _calculate_total(order_request: OrderCreateRequest):
    return Decimal(sum(item.quantity * item.price for item in order_request.items))


class OrderService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.user = current_user
        self.order_dao = OrderDAO(Order, db)

    async def create_new_order(self, order_request: OrderCreateRequest):
        total_price = _calculate_total(order_request)

        order_data = order_request.model_dump(exclude_unset=True)
        order_data["items"] = [item.model_dump() for item in order_request.items]

        order_dict = {
            "items": order_data["items"],
            "total_price": total_price,
            "status": order_data["status"] or "PENDING",
        }

        order = await self.order_dao.create(order_dict, user_id=self.user.id)

        return order

    async def get_order_by_id(self, db: AsyncSession, order_id: UUID):
        user_id = self.user.id

        order = await get_or_set(
            db,
            order_id,
        )

        if not order:
            raise HTTPException(status_code=404, detail={"message": "Order not found"})

        if isinstance(order, Order):
            if order.user_id != user_id:
                raise HTTPException(403, "Access denied")
            return order

        if order["user_id"] != user_id:
            raise HTTPException(403, "Access denied")
        return OrderResponse(**order)

    async def update_order_status(
        self, order_id: UUID, update_data: OrderStatusUpdate, user_id: int
    ):
        order_dao = OrderDAO(Order, self.db)

        # Получаем заказ из БД
        db_order = await order_dao.get(id=order_id)

        if not db_order:
            raise HTTPException(404, detail="Заказ не найден")

        if db_order.user_id != user_id:
            raise HTTPException(400, detail="Not yours order")

        # Проверяем допустимый статус
        allowed_statuses = {"pending", "paid", "shipped", "canceled"}
        if update_data.status not in allowed_statuses:
            raise HTTPException(
                400,
                detail=f"Invalid status: {', '.join(allowed_statuses)}",
            )

        # Обновляем в базе
        updated_order = await order_dao.update(
            id=order_id, obj_in={"status": update_data.status}
        )

        if not updated_order:
            raise HTTPException(
                500,
                detail="Error while updating status",
            )

        # Инвалидируем кэш
        await invalidate_order_cache(order_id)

        return updated_order

    async def get_user_orders(self):
        order_dao = OrderDAO(Order, self.db)

        orders = await order_dao.get_user_orders(user_id=self.user.id)

        if not orders:
            return []

        orders_sorted = sorted(orders, key=lambda o: o.created_at, reverse=True)

        return orders_sorted
