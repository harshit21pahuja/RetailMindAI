from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

# Async Engine for FastAPI async requests
# SQLite needs check_same_thread=False
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Synchronous Engine for Seed Scripts & Data Migrations
sync_connect_args = {}
if settings.SYNC_DATABASE_URL.startswith("sqlite"):
    sync_connect_args = {"check_same_thread": False}

sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    connect_args=sync_connect_args,
    future=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables asynchronously."""
    from backend.models import (  # noqa: F401
        product,
        inventory,
        sales,
        forecast,
        reorder,
        alert,
    )
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db_sync() -> None:
    """Create tables synchronously (for standalone scripts/seeders)."""
    from backend.models import (  # noqa: F401
        product,
        inventory,
        sales,
        forecast,
        reorder,
        alert,
    )
    Base.metadata.create_all(bind=sync_engine)
