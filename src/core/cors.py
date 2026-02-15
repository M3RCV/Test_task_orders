from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings


def setup_cors(app: FastAPI) -> FastAPI:
    """Базовый CORS middleware, можно расширять"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_origins,
        allow_credentials=settings.backend_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app