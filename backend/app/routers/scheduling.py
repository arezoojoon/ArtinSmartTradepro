from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user
from app.models.scheduling import Appointment, AvailabilitySlot
from app.services.scheduling_service import SchedulingService
from pydantic import BaseModel
import uuid
import datetime

router = APIRouter()

# --- Schemas ---

class AvailabilityCreate(BaseModel):
    user_id: str
    day_of_week: int   # 0=Mon ... 6=Sun
    start_time: str     # "09:00"
    end_time: str       # "17:00"

class AppointmentCreate(BaseModel):
    host_id: str
    guest_name: str
    guest_email: Optional[str] = None
    start_time: str     # ISO datetime "2026-02-15T10:00:00"
    end_time: str       # ISO datetime "2026-02-15T11:00:00"
    meeting_type: str   # "online" | "in_person"
    location: Optional[str] = None
    notes: Optional[str] = None

# --- Availability ---

@router.get("/availability/{user_id}")
def get_availability(user_id: str, db: Session = Depends(get_db)):
    return SchedulingService.get_user_availability(db, uuid.UUID(user_id))

@router.post("/availability")
def set_availability(
    data: AvailabilityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    start = datetime.time.fromisoformat(data.start_time)
    end = datetime.time.fromisoformat(data.end_time)
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    return SchedulingService.set_availability(
        db, tenant_id, uuid.UUID(data.user_id),
        data.day_of_week, start, end
    )

@router.delete("/availability/{slot_id}")
def delete_availability(slot_id: str, db: Session = Depends(get_db)):
    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == uuid.UUID(slot_id)).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    slot.is_active = False
    db.commit()
    return {"status": "deleted"}

# --- Slots ---

@router.get("/slots/{user_id}")
def get_free_slots(user_id: str, date: str, db: Session = Depends(get_db)):
    """
    Returns available booking slots for a given user on a given date.
    date format: YYYY-MM-DD
    """
    target_date = datetime.date.fromisoformat(date)
    slots = SchedulingService.get_available_slots(db, uuid.UUID(user_id), target_date)
    return slots

# --- Appointments ---

@router.get("/appointments/{user_id}")
def get_appointments(user_id: str, db: Session = Depends(get_db)):
    return SchedulingService.get_upcoming_appointments(db, uuid.UUID(user_id))

@router.post("/appointments")
def book_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    try:
        appt = SchedulingService.book_appointment(
            db, tenant_id,
            host_id=uuid.UUID(data.host_id),
            guest_name=data.guest_name,
            guest_email=data.guest_email,
            start_time=datetime.datetime.fromisoformat(data.start_time),
            end_time=datetime.datetime.fromisoformat(data.end_time),
            meeting_type=data.meeting_type,
            location=data.location,
            notes=data.notes
        )
        return appt
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.patch("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: str, db: Session = Depends(get_db)):
    try:
        return SchedulingService.cancel_appointment(db, uuid.UUID(appointment_id))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
