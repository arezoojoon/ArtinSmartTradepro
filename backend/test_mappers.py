import app.models
from sqlalchemy.orm import configure_mappers
print("Configuring mappers...")
configure_mappers()
print("Success!")
