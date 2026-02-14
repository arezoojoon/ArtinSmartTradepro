import logging
import sys
import os
import asyncio

# Add parent dir to path so we can import 'app'
# This is critical for Docker execution
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models.base import Base

# Import all models to ensure they are registered with Base.metadata
# This registration is what allows create_all to see all tables and resolve ForeignKeys
from app import models  # noqa

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    try:
        logger.info("Creating initial database tables...")
        
        # Get sync database URL for init_db
        settings = get_settings()
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        
        # Create sync engine for init_db
        sync_engine = create_engine(db_url)
        
        # Create all tables
        # SQLAlchemy handles dependency order automatically if all models are imported
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Database tables created successfully!")
        
        # Verify connection
        with sync_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"Database connection verified: {result.scalar()}")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        # We don't exit(1) here because we want the container to keep running 
        # even if init fails (e.g. if tables already exist)
        # sys.exit(1) 

if __name__ == "__main__":
    init_db()
