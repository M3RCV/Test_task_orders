from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dao.orders_dao import OrderDAO
from src.db.models.order import Order
from src.db.models.user import User
from src.db.redis.redis_utils import get_or_set
from src.schemas.response.order import OrderCreateRequest, OrderResponse


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
            "status": order_data["status"] or "PENDING"
        }

        order = await self.order_dao.create(
            order_dict,
            user_id=self.user.id
        )

        return order

    async def get_order_by_id(self, db: AsyncSession, order_id: UUID):
        user_id = self.user.id

        order = await get_or_set(
            db,
            order_id,
        )

        if not order:
            raise HTTPException(
                status_code=404,
                detail={"message": "Order not found"}
            )

        if isinstance(order, Order):
            if order.user_id != user_id:
                raise HTTPException(403, "Access denied")
            return order

        if order["user_id"] != user_id:
            raise HTTPException(403, "Access denied")
        return OrderResponse(**order)



