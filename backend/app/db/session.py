"""
Tenant-aware database session — Phase 1 Architecture.
Injects SET LOCAL app.tenant_id for PostgreSQL RLS enforcement.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from contextvars import ContextVar

from ..core.config import settings

# Context variable to hold current tenant_id per request
current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default=None)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    Automatically sets PostgreSQL session variable for RLS
    if a tenant_id is present in the context.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Inject tenant context for RLS
            tenant_id = current_tenant_id.get(None)
            if tenant_id:
                await session.execute(
                    text(f"SET LOCAL app.tenant_id = '{tenant_id}'")
                )
            yield session
        finally:
            await session.close()


async def get_db_no_tenant() -> AsyncSession:
    """
    Dependency for endpoints that don't require tenant context
    (e.g. registration, super admin operations).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
