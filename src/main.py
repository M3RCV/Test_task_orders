from fastapi import FastAPI
from starlette.responses import HTMLResponse

from src.api.router.endponts.auth import router_auth
from src.api.router.endponts.orders import router_order
from src.core.kafka import lifespan_producer

app = FastAPI(
    lifespan=lifespan_producer,
    title="Сервис управления заказами",
    description="Тестовое задание: FastAPI + PostgreSQL + Redis + Kafka + Celery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <h1 style="text-align: center; margin-top: 50px;">Сервис управления заказами</h1>
    <p style="text-align: center; font-size: 1.2em;">
        Добро пожаловать! Это API-сервис.<br>
        Интерактивная документация и тестирование доступны здесь:<br><br>
        <a href="/docs" style="font-size: 1.5em; color: #0066cc;">Перейти в Swagger UI →</a>
    </p>
    <p style="text-align: center; margin-top: 40px; color: #666;">
        ID заказов — автоматически генерируемые UUID v4
    </p>
    """

app.include_router(router_auth, prefix="/api/v1/auth", tags=["auth"])
app.include_router(router_order, prefix="/api/v1/orders", tags=["orders"])
