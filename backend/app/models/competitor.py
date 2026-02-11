from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Numeric, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class Competitor(Base):
    """
    Represents a direct or indirect competitor in the market.
    """
    __tablename__ = "competitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False, index=True)
    website = Column(String, nullable=True)
    country = Column(String, nullable=True, index=True) # ISO2 or ISO3
    
    # Strategic Attributes
    industry_tags = Column(JSON, default=list) # e.g. ["ceramics", "petrochemicals"]
    threat_level = Column(String, default="medium") # low, medium, high, critical
    is_active = Column(Boolean, default=True)
    
    # Market Positioning
    market_share_est = Column(Numeric(5, 2), nullable=True) # Percentage
    pricing_strategy = Column(String, nullable=True) # premium, budget, market_leader
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    products = relationship("CompetitorProduct", back_populates="competitor", cascade="all, delete-orphan")
    market_share_snapshots = relationship("MarketShareSnapshot", back_populates="competitor", cascade="all, delete-orphan")


class CompetitorProduct(Base):
    """
    A specific product offered by a competitor, tracked for price and availability.
    """
    __tablename__ = "competitor_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    sku = Column(String, nullable=True) # For de-duplication if available
    external_product_id = Column(String, nullable=True) # ID on source site
    product_url = Column(String, nullable=True)
    
    # Current State (Last Observation)
    availability_status = Column(String, default="unknown") # in_stock, out_of_stock, unknown
    shipping_cost_estimate = Column(Numeric(10, 2), nullable=True)
    min_order_qty = Column(Integer, nullable=True)
    observed_source = Column(String, nullable=True) # alibaba, website, amazon
    
    last_price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String, default="USD")
    last_observed_at = Column(DateTime, nullable=True)
    
    specifications = Column(JSON, nullable=True) # Tech specs for comparison

    competitor = relationship("Competitor", back_populates="products")
    price_history = relationship("CompetitorPriceObservation", back_populates="product", cascade="all, delete-orphan")


class CompetitorPriceObservation(Base):
    """
    Time-series record of price observations for trend analysis.
    """
    __tablename__ = "competitor_price_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_product_id = Column(UUID(as_uuid=True), ForeignKey("competitor_products.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    
    observed_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # Evidence & Metadata
    raw_payload = Column(JSON, nullable=True) # Snapshot of HTML or API response
    confidence_score = Column(Numeric(3, 2), default=1.0) # 0.0 to 1.0 (Scrapers might be noisy)

    product = relationship("CompetitorProduct", back_populates="price_history")


class MarketShareSnapshot(Base):
    """
    Time-series snapshot of estimated market share based on various signals.
    """
    __tablename__ = "market_share_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    share_percentage = Column(Numeric(5, 2), nullable=False) # e.g. 15.5%
    trend = Column(String, nullable=True) # up, down, stable
    
    # Signal Source
    signal_type = Column(String, nullable=True) # traffic, mentions, ad_spend, import_volume
    source_name = Column(String, nullable=True) # similarweb, google_trends, customs_data
    confidence_score = Column(Numeric(3, 2), default=0.8)

    competitor = relationship("Competitor", back_populates="market_share_snapshots")
