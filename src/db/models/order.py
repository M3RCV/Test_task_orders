from sqlalchemy import String, Float, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from typing import TYPE_CHECKING, Dict, List, Any

from src.db.base import BaseUUID

if TYPE_CHECKING:
    from src.db.models.user import User


class OrderStatus(str, enum.Enum):
    """Статусы заказа согласно ТЗ"""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELED = "canceled"


class Order(BaseUUID):
    """Модель заказа"""

    __tablename__ = "orders"

    # Внешний ключ на пользователя (как в ТЗ: user_id int, ForeignKey на пользователей)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Товары в JSON формате (как в ТЗ: items (JSON, список товаров))
    items: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    # Общая цена (как в ТЗ: total_price (float))
    total_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Статус заказа (как в ТЗ: status (enum: PENDING, PAID, SHIPPED, CANCELED))
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )

    # Связь с пользователем
    user: Mapped["User"] = relationship(
        "User",
        back_populates="orders",
        lazy="joined"  # Всегда загружаем пользователя с заказом
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"

    @property
    def items_count(self) -> int:
        """Количество товаров в заказе"""
        return len(self.items) if self.items else 0

    @property
    def is_pending(self) -> bool:
        """Проверка, что заказ в ожидании"""
        return self.status == OrderStatus.PENDING

    @property
    def can_be_canceled(self) -> bool:
        """Можно ли отменить заказ"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PAID]