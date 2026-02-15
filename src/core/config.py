from pathlib import Path
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# путь к корню проекта
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    # ======================
    # База данных
    # ======================
    database_url: str

    # ======================
    # Redis
    # ======================
    redis_url: str
    redis_cache_ttl: int = 300

    # ======================
    # Kafka
    # ======================
    kafka_bootstrap_servers: str
    kafka_topic: str
    kafka_consumer_group: str

    # ======================
    # Celery
    # ======================
    celery_broker_url: str
    celery_result_backend: str

    # ======================
    # JWT
    # ======================
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ======================
    # Приложение
    # ======================
    debug: bool = False
    cors_origins: List[str] = []
    rate_limit_per_minute: int = 60

    # ======================
    # CORS
    # ======================
    backend_origins: str
    backend_allow_credentials: bool

    # ======================
    # Проект
    # ======================
    project_name: str = "Order Management Service"
    api_v1_prefix: str = "/api/v1"

    # ======================
    # Парсинг списков из ENV
    # ======================
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    # ======================
    # Config Pydantic v2
    # ======================
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # игнорировать POSTGRES_* из docker
    )


# ======================
# Singleton settings
# ======================

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
