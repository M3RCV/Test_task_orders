# migrations/env.py
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

import sys
import os

# ⚠️ КРИТИЧЕСКИ ВАЖНО: Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ⚠️ Импортируем НАШИ модели и настройки
from src.core.config import settings
from src.db.base import Base
from src.db.models import order, user

# Загружаем конфигурацию Alembic
config = context.config

# Настраиваем логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Указываем метаданные для автогенерации миграций
target_metadata = Base.metadata


# Получаем URL базы данных ИЗ НАШИХ настроек (не из alembic.ini)
def get_url():
    return settings.database_url


def run_migrations_offline() -> None:
    """Запуск миграций в оффлайн режиме (без подключения к БД)"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Запуск миграций через подключение"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Асинхронный запуск миграций"""
    # Создаем engine из настроек Alembic
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск миграций в онлайн режиме"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()