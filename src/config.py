import os
from loguru import logger
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    환경 세팅을 위한 Static Class
    """

    PROJECT_NAME: str = "template"
    MAINTAINER_EMAIL: str = "keyog@buzzni.com"

    ENV: str = "local"
    DEBUG_MODE: bool = True
    API_VERSION: str = "0.0.1"
    DOMAIN: str = "localhost"

    # RDB
    RDB_URI: str = "sqlite:///local.db"
    RDB_ASYNC_URI: str = "sqlite+aiosqlite:///local.db"
    POSTGRES_URI: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    POSTGRES_ASYNC_URI: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

    # Cache
    CACHE_URI: str = "mem://"
    # CACHE_URI: str = "redis://localhost:6379"

    # JWT
    API_KEY_SECRET: str = "your_api_key_secret"
    ACCESS_TOKEN_SECRET: str = "your_access_token_secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_SECRET: str = "your_refresh_token_secret"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # PASS
    PASS_CLIENT_ID: str = "your_pass_client_id"
    PASS_CLIENT_SECRET: str = "your_pass_client_secret"
    PASS_REDIRECT_URI: str = "your_pass_redirect_uri"
    PASS_TOKEN_VERSION_ID: str = "your_pass_token_version_id"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
logger.info("ENV: {}", settings.ENV)
logger.info("DEBUG: {}", settings.DEBUG_MODE)
logger.info("API_VERSION: {}", settings.API_VERSION)
