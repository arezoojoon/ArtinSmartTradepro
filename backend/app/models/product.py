from sqlalchemy import Column, String, Float, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import relationship
from .base import Base

from sqlalchemy.dialects.postgresql import UUID

class Product(Base):
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))

    name = Column(String, index=True)
    sku = Column(String, index=True, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String, index=True, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    stock_quantity = Column(Integer, default=0)

    images = Column(JSON, default=[])
    specifications = Column(JSON, default={})

    tenant = relationship("Tenant", back_populates="products")

# RFQ model moved to models/sourcing.py to avoid duplicate table 'rfqs' registration
