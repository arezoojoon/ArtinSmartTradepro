from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

# Normalize DATABASE_URL for synchronous engine
# Docker production sets postgresql+asyncpg:// but this module uses sync create_engine
_sync_url = settings.DATABASE_URL
if "+asyncpg" in _sync_url:
    _sync_url = _sync_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
elif _sync_url.startswith("postgresql://"):
    pass  # Already compatible with sync

engine = create_engine(
    _sync_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,  # Recycle connections every 30 minutes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.models.base import Base

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
