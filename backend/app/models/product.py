from sqlalchemy import Column, String, Float, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Product(Base):
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    
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

class RFQ(Base):
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    
    title = Column(String, index=True)
    description = Column(Text)
    status = Column(String, default="open")  # open, quoted, awarded, closed
    budget = Column(Float, nullable=True)
    deadline = Column(String, nullable=True)
    
    tenant = relationship("Tenant")
