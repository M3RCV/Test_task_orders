from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from src.core.config import settings

# ── Настройки ────────────────────────────────────────────────
DATABASE_URL = settings.database_url

# Создаём движок
engine = create_async_engine(
    DATABASE_URL,
    # очень полезные параметры (рекомендую)
    echo=False,                     # True → будет показывать все SQL-запросы
    future=True,
    pool_pre_ping=True,             # проверяет соединение перед выдачей из пула
    pool_size=5,
    max_overflow=10,
)


# Фабрика сессий (самый удобный способ)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False          # очень важно для FastAPI
)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


