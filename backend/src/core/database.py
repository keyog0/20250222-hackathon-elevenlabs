from contextlib import contextmanager
from loguru import logger
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.core.retry_query import AsyncRetryingQuery, RetryingQuery
from src.config import settings

Base = declarative_base()

if settings.ENV in ["local", "test"]:
    async_engine = create_async_engine(
        settings.RDB_ASYNC_URI,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    engine = create_engine(
        settings.RDB_URI,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    async_engine = create_async_engine(
        settings.POSTGRES_ASYNC_URI,
        echo=settings.DEBUG_MODE,
        future=True,
        max_overflow=10,
        pool_size=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={"application_name": f"{settings.PROJECT_NAME}-{settings.ENV}"},
    )

    engine = create_engine(
        settings.POSTGRES_ASYNC_URI,
        max_overflow=10,
        pool_size=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={"application_name": f"{settings.PROJECT_NAME}-{settings.ENV}"},
    )

AsyncSessionLocal = sessionmaker(
    async_engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    query_cls=AsyncRetryingQuery,
    expire_on_commit=False,
)
SessionLocal = sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
    query_cls=RetryingQuery,
    expire_on_commit=False,
)


async def get_async_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            await session.close()


def get_session():
    with SessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()


@contextmanager
def get_session_context():
    with SessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()
