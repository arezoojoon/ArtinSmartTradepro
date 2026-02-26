"""
Smart Logistics Models — Shipment tracking, packages, events, carriers.
AI Vision-powered document extraction for zero-touch data entry.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, ForeignKey, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base
import uuid
import enum


class ShipmentStatus(str, enum.Enum):
    created = "created"
    picked = "picked"
    assigned = "assigned"
    pickup_confirmed = "pickup_confirmed"
    in_transit = "in_transit"
    at_hub = "at_hub"
    out_for_delivery = "out_for_delivery"
    delivery_attempt = "delivery_attempt"
    delivered = "delivered"
    failed_delivery = "failed_delivery"
    returned = "returned"
    damaged = "damaged"
    cancelled = "cancelled"


class ShipmentEventType(str, enum.Enum):
    created = "created"
    picked_up_from_factory = "picked_up_from_factory"
    assigned_to_carrier = "assigned_to_carrier"
    pickup_confirmed = "pickup_confirmed"
    in_transit = "in_transit"
    at_hub = "at_hub"
    out_for_delivery = "out_for_delivery"
    delivery_attempt = "delivery_attempt"
    delivered = "delivered"
    failed_delivery = "failed_delivery"
    returned = "returned"
    damaged = "damaged"
    cancelled = "cancelled"
    telemetry = "telemetry"
    delay_alert = "delay_alert"
    note = "note"


class Carrier(Base):
    __tablename__ = "logistics_carriers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    contact_name = Column(String)
    contact_phone = Column(String)
    contact_email = Column(String)
    api_endpoint = Column(String)
    capabilities = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    shipments = relationship("Shipment", back_populates="carrier")


class Shipment(Base):
    __tablename__ = "logistics_shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    shipment_number = Column(String, nullable=False, index=True)
    order_id = Column(String)

    # Origin & Destination (JSON: {city, country, address, lat, lng})
    origin = Column(JSONB, default={})
    destination = Column(JSONB, default={})

    status = Column(String, default="created", nullable=False, index=True)
    carrier_id = Column(UUID(as_uuid=True), ForeignKey("logistics_carriers.id"), nullable=True)

    # Goods description
    goods_description = Column(Text)
    total_weight_kg = Column(Float)
    total_packages = Column(Integer, default=0)
    incoterms = Column(String)

    # Timing
    estimated_delivery = Column(DateTime(timezone=True))
    actual_delivery = Column(DateTime(timezone=True))
    pickup_at = Column(DateTime(timezone=True))

    # POD (proof of delivery)
    pod_image_url = Column(String)
    pod_signature_url = Column(String)
    pod_recipient_name = Column(String)

    # AI extraction metadata
    ai_extracted = Column(Boolean, default=False)
    ai_confidence = Column(Float)
    source_document_url = Column(String)

    # Customer notification
    customer_phone = Column(String)
    customer_name = Column(String)
    notification_sent = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    carrier = relationship("Carrier", back_populates="shipments")
    packages = relationship("ShipmentPackage", back_populates="shipment", cascade="all, delete-orphan")
    events = relationship("ShipmentEvent", back_populates="shipment", cascade="all, delete-orphan", order_by="ShipmentEvent.timestamp.desc()")


class ShipmentPackage(Base):
    __tablename__ = "logistics_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("logistics_shipments.id", ondelete="CASCADE"), nullable=False)
    barcode = Column(String)
    weight_kg = Column(Float)
    dimensions = Column(String)
    contents = Column(Text)
    metadata_json = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    shipment = relationship("Shipment", back_populates="packages")


class ShipmentEvent(Base):
    __tablename__ = "logistics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("logistics_shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id = Column(UUID(as_uuid=True), ForeignKey("logistics_packages.id"), nullable=True)

    event_type = Column(String, nullable=False, index=True)
    actor = Column(String)  # factory:plant-42, carrier:FastLogistics, system
    payload = Column(JSONB, default={})

    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String)

    # Telemetry
    speed_kmh = Column(Float)
    eta = Column(DateTime(timezone=True))

    notes = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    shipment = relationship("Shipment", back_populates="events")
