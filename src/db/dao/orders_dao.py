from typing import List
from sqlalchemy import select
from src.db.dao.dao import BaseDAO
from src.db.models.order import Order, OrderStatus


class OrderDAO(BaseDAO[Order]):
    async def get_user_orders(self, user_id: int) -> List[Order]:
        result = await self.session.execute(
            select(Order).where(Order.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: OrderStatus) -> List[Order]:
        result = await self.session.execute(
            select(Order).where(Order.status == status)
        )
        return list(result.scalars().all())