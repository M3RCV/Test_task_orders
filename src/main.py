from fastapi import FastAPI

from src.api.router.endponts.health import router
from src.api.router.endponts.auth import router_auth

app = FastAPI(
    title='test_task',
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router_auth, prefix="/api/v1/auth", tags=["auth"])
app.include_router(router, prefix="/api/v1/health", tags=["health"])