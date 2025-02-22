import logging

from cashews import cache
from cashews.contrib.fastapi import (
    CacheDeleteMiddleware,
    CacheEtagMiddleware,
    CacheRequestControlMiddleware,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from router.api import api_router
from config import settings
from middlewares.logging import LoggingMiddleware
from core.errors.exceptions import CustomException
from core.errors.handlers import custom_exception_handler, general_error_handler, http_exception_handler
from script.setup_database import setup_database


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if (
            "GET" in record.getMessage()
            or "POST" in record.getMessage()
            or "PUT" in record.getMessage()
            or "PATCH" in record.getMessage()
            or "DELETE" in record.getMessage()
        ):
            return False  # 기본 로그 메시지를 무시
        return record.getMessage().find("/healthcheck") == -1


def create_app():
    app = FastAPI(version=settings.API_VERSION, title=f"Fast API ({settings.ENV})")
    # origins = ["*", "http://localhost", "http://localhost:8887", "http://0.0.0.0"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(CacheDeleteMiddleware)
    app.add_middleware(CacheEtagMiddleware)
    app.add_middleware(CacheRequestControlMiddleware)
    cache.setup(settings.CACHE_URI)

    app.include_router(api_router)

    app.add_exception_handler(Exception, general_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(CustomException, custom_exception_handler)

    if settings.ENV == "local":
        setup_database()

    return app


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
app = create_app()
