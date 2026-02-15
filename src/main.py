from fastapi import FastAPI

from src.api.router.endponts.auth import router_auth
from src.api.router.endponts.orders import router_order
from src.core.kafka import lifespan_producer

app = FastAPI(
    lifespan=lifespan_producer,
    title="test_task",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router_auth, prefix="/api/v1/auth", tags=["auth"])
app.include_router(router_order, prefix="/api/v1/orders", tags=["orders"])
