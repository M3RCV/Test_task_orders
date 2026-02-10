from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncpg
import logging

from src.db.session import get_db
from src.core.config import settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """Базовая проверка здоровья приложения"""
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": "1.0.0"
    }


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Проверка подключения к базе данных"""
    try:
        # Простой запрос к БД
        result = await db.execute(text("SELECT 1 as test"))
        row = result.fetchone()

        if row and row[0] == 1:
            return {
                "status": "healthy",
                "database": "connected",
                "message": "Database connection successful"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database query failed"
            )

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )