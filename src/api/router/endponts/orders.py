from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.router.endponts.auth import get_current_active_user
from src.core.kafka import publish_new_order
from src.db.dao.orders_dao import OrderDAO
from src.db.models.order import Order
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.request.order import OrderCreateRequest
from src.schemas.response.order import OrderResponse
from uuid import UUID
import json
from dotenv import load_dotenv
import os

#load_dotenv()
#RABBITMQ_URL = os.getenv("RABBITMQ_URL")

router_order = APIRouter(
    prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_active_user)]
)


# def publish_to_queue(order_id: str):
#     params = pika.URLParameters(RABBITMQ_URL)
#     connection = pika.BlockingConnection(params)
#     channel = connection.channel()
#     channel.queue_declare(queue="new_order")
#     channel.basic_publish(exchange="", routing_key="new_order", body=order_id)
#     connection.close()


@router_order.post("/", response_model=OrderResponse)
async def create_order_endpoint(
    order_request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    order_dao = OrderDAO(Order, db)
    order_dict = {
        "items": order_request.items,
        "total_price": order_request.total_price,
        "status": order_request.status
    }
    order = await order_dao.create(
        order_dict,
        user_id = current_user.id,
    )
    await publish_new_order(str(order.id), current_user.id)
    return OrderResponse.from_orm(order)


# @router_order.get("/{order_id}/", response_model=OrderResponse)
# def get_order_endpoint(
#     order_id: UUID, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)
# ):
#     cached_order = redis.get(str(order_id))
#     if cached_order:
#         return json.loads(cached_order)
#     db_order = get_order(db, order_id)
#     if not db_order:
#         raise HTTPException(status_code=404, detail="Order not found")
#     redis.set(str(order_id), json.dumps(db_order.__dict__), ex=300)  # TTL 5 min
#     return db_order
#
#
# @router.patch("/{order_id}/", response_model=OrderOut)
# @limiter.limit("10/minute")
# def update_order_endpoint(
#     order_id: UUID,
#     order_update: OrderUpdate,
#     db: Session = Depends(get_db),
#     redis=Depends(get_redis),
#     current_user=Depends(get_current_user),
# ):
#     db_order = update_order(db, order_id, order_update)
#     if not db_order:
#         raise HTTPException(status_code=404, detail="Order not found")
#     redis.set(str(order_id), json.dumps(db_order.__dict__), ex=300)  # Update cache
#     return db_order
#
#
# @router.get("/user/{user_id}/", response_model=List[OrderOut])
# @limiter.limit("10/minute")
# def get_user_orders_endpoint(
#     user_id: int, db: Session = Depends(get_db)
# ):
#     if current_user.id != user_id:
#         raise HTTPException(status_code=403, detail="Not authorized")
#     return get_user_orders(db, user_id)
