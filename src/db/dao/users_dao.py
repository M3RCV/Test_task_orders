from sqlalchemy import select

from src.db.dao.dao import BaseDAO
from src.db.models.user import User


class UserDAO(BaseDAO[User]):
    async def get_by_email(self, email: str):
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()