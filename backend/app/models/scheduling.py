import uuid
import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Time, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class AvailabilitySlot(Base):
    """
    Defines when a user is available for meetings.
    Example: Monday 9:00-12:00, Monday 14:00-17:00
    """
    __tablename__ = "availability_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    start_time = Column(Time, nullable=False)       # e.g. 09:00
    end_time = Column(Time, nullable=False)          # e.g. 12:00
    is_active = Column(Boolean, default=True)

    user = relationship("User", foreign_keys=[user_id])


class Appointment(Base):
    """
    A booked meeting between a host (internal user) and a guest.
    Supports both online and in-person meetings.
    """
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    guest_name = Column(String, nullable=False)
    guest_email = Column(String, nullable=True)
    guest_phone = Column(String, nullable=True)

    # Time
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # Type
    meeting_type = Column(String, default="online")  # online | in_person
    location = Column(String, nullable=True)          # Physical address or video link

    # Status
    status = Column(String, default="scheduled")  # scheduled | cancelled | completed
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    host = relationship("User", foreign_keys=[host_id])
