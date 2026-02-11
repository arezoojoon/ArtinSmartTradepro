from sqlalchemy.orm import Session
from app.models.scheduling import AvailabilitySlot, Appointment
import uuid
import datetime


class SchedulingService:
    """
    Manages availability slots and appointment booking.
    """

    @staticmethod
    def set_availability(db: Session, tenant_id: uuid.UUID, user_id: uuid.UUID,
                         day_of_week: int, start_time: datetime.time, end_time: datetime.time):
        """
        Sets a user's availability for a specific day of the week.
        """
        slot = AvailabilitySlot(
            tenant_id=tenant_id,
            user_id=user_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_active=True
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)
        return slot

    @staticmethod
    def get_user_availability(db: Session, user_id: uuid.UUID):
        """
        Returns all active availability slots for a user.
        """
        return db.query(AvailabilitySlot).filter(
            AvailabilitySlot.user_id == user_id,
            AvailabilitySlot.is_active == True
        ).all()

    @staticmethod
    def get_available_slots(db: Session, user_id: uuid.UUID, date: datetime.date):
        """
        Returns available time slots for a specific date,
        excluding already booked appointments.
        """
        day_of_week = date.weekday()  # 0=Monday

        # 1. Get availability for this day
        availability = db.query(AvailabilitySlot).filter(
            AvailabilitySlot.user_id == user_id,
            AvailabilitySlot.day_of_week == day_of_week,
            AvailabilitySlot.is_active == True
        ).all()

        if not availability:
            return []

        # 2. Get existing appointments for this date
        start_of_day = datetime.datetime.combine(date, datetime.time.min)
        end_of_day = datetime.datetime.combine(date, datetime.time.max)

        booked = db.query(Appointment).filter(
            Appointment.host_id == user_id,
            Appointment.start_time >= start_of_day,
            Appointment.end_time <= end_of_day,
            Appointment.status != "cancelled"
        ).all()

        booked_times = set()
        for appt in booked:
            hour = appt.start_time.hour
            booked_times.add(hour)

        # 3. Generate hourly slots, minus booked
        free_slots = []
        for slot in availability:
            current_hour = slot.start_time.hour
            end_hour = slot.end_time.hour
            while current_hour < end_hour:
                if current_hour not in booked_times:
                    slot_start = datetime.datetime.combine(date, datetime.time(current_hour, 0))
                    slot_end = datetime.datetime.combine(date, datetime.time(current_hour + 1, 0))
                    free_slots.append({
                        "start": slot_start.isoformat(),
                        "end": slot_end.isoformat(),
                        "label": f"{current_hour:02d}:00"
                    })
                current_hour += 1

        return free_slots

    @staticmethod
    def book_appointment(db: Session, tenant_id: uuid.UUID, host_id: uuid.UUID,
                         guest_name: str, guest_email: str,
                         start_time: datetime.datetime, end_time: datetime.datetime,
                         meeting_type: str = "online", location: str = None,
                         notes: str = None):
        """
        Books an appointment. Validates no double-booking.
        """
        # Check for conflicts
        conflict = db.query(Appointment).filter(
            Appointment.host_id == host_id,
            Appointment.status != "cancelled",
            Appointment.start_time < end_time,
            Appointment.end_time > start_time
        ).first()

        if conflict:
            raise Exception(f"Time conflict with existing appointment at {conflict.start_time}")

        appointment = Appointment(
            tenant_id=tenant_id,
            host_id=host_id,
            guest_name=guest_name,
            guest_email=guest_email,
            start_time=start_time,
            end_time=end_time,
            meeting_type=meeting_type,
            location=location,
            notes=notes,
            status="scheduled"
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def cancel_appointment(db: Session, appointment_id: uuid.UUID):
        """
        Cancels an appointment by ID.
        """
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise Exception("Appointment not found")
        appt.status = "cancelled"
        db.commit()
        return appt

    @staticmethod
    def get_upcoming_appointments(db: Session, user_id: uuid.UUID):
        """
        Returns all upcoming appointments for a user (as host).
        """
        now = datetime.datetime.utcnow()
        return db.query(Appointment).filter(
            Appointment.host_id == user_id,
            Appointment.start_time >= now,
            Appointment.status == "scheduled"
        ).order_by(Appointment.start_time.asc()).all()
