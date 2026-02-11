from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Boolean, Float, Text
from sqlalchemy.orm import relationship
from .base import Base

class MarketplaceListing(Base):
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    title = Column(String, index=True)  # Override product name if needed
    description = Column(Text)
    
    reviews = Column(JSON, default=[])
    rating = Column(Float, default=0.0)
    
    tenant = relationship("Tenant")
    product = relationship("Product")
