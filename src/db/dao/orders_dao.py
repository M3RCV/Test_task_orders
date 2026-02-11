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

    async def create(self, obj_in: dict, user_id: int) -> Order:
        create_data = obj_in.copy()           # чтобы не менять оригинальный словарь
        create_data["user_id"] = user_id
        db_obj = self.model(**create_data)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj