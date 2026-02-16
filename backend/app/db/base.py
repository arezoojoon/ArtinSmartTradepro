from app.models.base import Base

# Import all models here so Alembic or other tools can discover them
# This file serves as a central registry for all models
from app.models.email import EmailOutbox
