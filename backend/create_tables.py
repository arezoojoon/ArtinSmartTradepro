import sys
import os
# Ensure backend is in path
sys.path.append("/app")

from app.database import engine
from app.models.base import Base
# Import all models to ensure they are registered with Base.metadata
from app.models import *

def create_tables():
    print(f"Connecting to: {engine.url}")
    print(f"Tables to create: {list(Base.metadata.tables.keys())}")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()
