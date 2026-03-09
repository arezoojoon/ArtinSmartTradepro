from sqlalchemy import Column, String, Float, ForeignKey, Integer, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import Base

from sqlalchemy.dialects.postgresql import UUID

class Product(Base):
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))

    name = Column(String, index=True)
    name_en = Column(String, nullable=True)
    name_ar = Column(String, nullable=True)
    name_ru = Column(String, nullable=True)
    
    sku = Column(String, index=True, unique=True, nullable=True)
    
    description = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    description_ru = Column(Text, nullable=True)
    
    category = Column(String, index=True, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, default="AED")
    stock_quantity = Column(Integer, default=0)

    features = Column(JSON, default=[]) # Extracted from Expo
    benefits = Column(JSON, default=[]) # Extracted from Expo
    selling_points = Column(JSON, default={}) # Extracted from Expo

    images = Column(JSON, default=[])
    image_url = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)

    tenant = relationship("Tenant")

# RFQ model moved to models/sourcing.py to avoid duplicate table 'rfqs' registration
