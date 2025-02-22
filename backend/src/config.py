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
    ELEVENLABS_API_KEY: str = "your_elevenlabs_api_key"
    
    # OpenAI
    OPENAI_API_KEY: str = "your_openai_api_key"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
logger.info("ENV: {}", settings.ENV)
logger.info("DEBUG: {}", settings.DEBUG_MODE)
logger.info("API_VERSION: {}", settings.API_VERSION)
