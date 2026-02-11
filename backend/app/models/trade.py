from sqlalchemy import Column, String, Float, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class Trade(Base):
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    status = Column(String, default="ongoing")  # ongoing, finalized, cancelled
    stage = Column(String, default="negotiation")  # negotiation, contract, payment, logistics
    
    total_value = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    
    tenant = relationship("Tenant", back_populates="trades")
    product = relationship("Product")
