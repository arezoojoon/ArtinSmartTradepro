"""
Smart Logistics Router — AI-powered shipment tracking & document extraction.
Zero-touch data entry via Vision AI (Gemini) for BL, packing lists, PODs.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.logistics import (
    Shipment, ShipmentPackage, ShipmentEvent, Carrier,
    ShipmentStatus, ShipmentEventType,
)
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
import uuid
import datetime
import base64
import logging
import json
import os

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Pydantic Schemas ───────────────────────────────────────────────

class LocationSchema(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class PackageCreate(BaseModel):
    barcode: Optional[str] = None
    weight_kg: Optional[float] = None
    dimensions: Optional[str] = None
    contents: Optional[str] = None

class ShipmentCreate(BaseModel):
    shipment_number: Optional[str] = None
    order_id: Optional[str] = None
    origin: Optional[LocationSchema] = None
    destination: Optional[LocationSchema] = None
    goods_description: Optional[str] = None
    total_weight_kg: Optional[float] = None
    incoterms: Optional[str] = None
    carrier_id: Optional[UUID] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    estimated_delivery: Optional[datetime.datetime] = None
    packages: Optional[List[PackageCreate]] = []

class ShipmentUpdate(BaseModel):
    status: Optional[str] = None
    carrier_id: Optional[UUID] = None
    goods_description: Optional[str] = None
    total_weight_kg: Optional[float] = None
    estimated_delivery: Optional[datetime.datetime] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None

class EventCreate(BaseModel):
    event_type: str
    actor: Optional[str] = None
    payload: Optional[dict] = {}
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    speed_kmh: Optional[float] = None
    eta: Optional[datetime.datetime] = None
    notes: Optional[str] = None
    package_id: Optional[UUID] = None

class CarrierCreate(BaseModel):
    name: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    api_endpoint: Optional[str] = None
    capabilities: Optional[dict] = {}


# ─── Helper: Generate shipment number ────────────────────────────────

def _generate_shipment_number() -> str:
    now = datetime.datetime.utcnow()
    return f"SHP-{now.year}-{uuid.uuid4().hex[:6].upper()}"


# ─── Helper: AI status mapping ───────────────────────────────────────

EVENT_TO_STATUS = {
    "created": "created",
    "picked_up_from_factory": "picked",
    "assigned_to_carrier": "assigned",
    "pickup_confirmed": "pickup_confirmed",
    "in_transit": "in_transit",
    "at_hub": "at_hub",
    "out_for_delivery": "out_for_delivery",
    "delivery_attempt": "delivery_attempt",
    "delivered": "delivered",
    "failed_delivery": "failed_delivery",
    "returned": "returned",
    "damaged": "damaged",
    "cancelled": "cancelled",
}


# ═══════════════════════════════════════════════════════════════════════
# SHIPMENTS CRUD
# ═══════════════════════════════════════════════════════════════════════

@router.get("/shipments")
async def list_shipments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all shipments for the tenant."""
    tenant_id = current_user.tenant_id
    stmt = select(Shipment).where(Shipment.tenant_id == tenant_id)

    if status:
        stmt = stmt.where(Shipment.status == status)
    if search:
        s = f"%{search}%"
        stmt = stmt.where(or_(
            Shipment.shipment_number.ilike(s),
            Shipment.goods_description.ilike(s),
            Shipment.customer_name.ilike(s),
        ))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    shipments = (await db.execute(
        stmt.order_by(desc(Shipment.created_at)).offset(skip).limit(limit)
    )).scalars().all()

    return {"total": total, "shipments": [_shipment_to_dict(s) for s in shipments]}


@router.post("/shipments")
async def create_shipment(
    body: ShipmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new shipment."""
    tenant_id = current_user.tenant_id
    shipment = Shipment(
        tenant_id=tenant_id,
        shipment_number=body.shipment_number or _generate_shipment_number(),
        order_id=body.order_id,
        origin=body.origin.dict() if body.origin else {},
        destination=body.destination.dict() if body.destination else {},
        goods_description=body.goods_description,
        total_weight_kg=body.total_weight_kg,
        incoterms=body.incoterms,
        carrier_id=body.carrier_id,
        customer_phone=body.customer_phone,
        customer_name=body.customer_name,
        estimated_delivery=body.estimated_delivery,
        status="created",
    )
    db.add(shipment)

    # Add packages
    if body.packages:
        shipment.total_packages = len(body.packages)
        for pkg in body.packages:
            p = ShipmentPackage(
                shipment_id=shipment.id,
                barcode=pkg.barcode,
                weight_kg=pkg.weight_kg,
                dimensions=pkg.dimensions,
                contents=pkg.contents,
            )
            db.add(p)

    # Create initial event
    ev = ShipmentEvent(
        shipment_id=shipment.id,
        event_type="created",
        actor=f"user:{current_user.id}",
        notes="Shipment created",
    )
    db.add(ev)

    await db.commit()
    await db.refresh(shipment)
    return _shipment_to_dict(shipment)


@router.get("/shipments/{shipment_id}")
async def get_shipment(
    shipment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get shipment with timeline."""
    tenant_id = current_user.tenant_id
    shipment = (await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Fetch events
    events = (await db.execute(
        select(ShipmentEvent)
        .where(ShipmentEvent.shipment_id == shipment_id)
        .order_by(desc(ShipmentEvent.timestamp))
    )).scalars().all()

    # Fetch packages
    packages = (await db.execute(
        select(ShipmentPackage).where(ShipmentPackage.shipment_id == shipment_id)
    )).scalars().all()

    result = _shipment_to_dict(shipment)
    result["events"] = [_event_to_dict(e) for e in events]
    result["packages"] = [_package_to_dict(p) for p in packages]
    return result


@router.patch("/shipments/{shipment_id}")
async def update_shipment(
    shipment_id: UUID,
    body: ShipmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update shipment fields."""
    tenant_id = current_user.tenant_id
    shipment = (await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    for field, val in body.dict(exclude_unset=True).items():
        setattr(shipment, field, val)

    await db.commit()
    await db.refresh(shipment)
    return _shipment_to_dict(shipment)


# ═══════════════════════════════════════════════════════════════════════
# EVENTS / TIMELINE
# ═══════════════════════════════════════════════════════════════════════

@router.post("/shipments/{shipment_id}/events")
async def add_event(
    shipment_id: UUID,
    body: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an event to shipment timeline and optionally update status."""
    tenant_id = current_user.tenant_id
    shipment = (await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    ev = ShipmentEvent(
        shipment_id=shipment_id,
        event_type=body.event_type,
        actor=body.actor or f"user:{current_user.id}",
        payload=body.payload or {},
        latitude=body.latitude,
        longitude=body.longitude,
        location_name=body.location_name,
        speed_kmh=body.speed_kmh,
        eta=body.eta,
        notes=body.notes,
        package_id=body.package_id,
    )
    db.add(ev)

    # Auto-update shipment status based on event type
    new_status = EVENT_TO_STATUS.get(body.event_type)
    if new_status:
        shipment.status = new_status
        if body.event_type == "delivered":
            shipment.actual_delivery = datetime.datetime.utcnow()

    await db.commit()
    return _event_to_dict(ev)


@router.get("/shipments/{shipment_id}/events")
async def list_events(
    shipment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full timeline for a shipment."""
    events = (await db.execute(
        select(ShipmentEvent)
        .where(ShipmentEvent.shipment_id == shipment_id)
        .order_by(desc(ShipmentEvent.timestamp))
    )).scalars().all()
    return [_event_to_dict(e) for e in events]


# ═══════════════════════════════════════════════════════════════════════
# CARRIERS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/carriers")
async def list_carriers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all carriers for the tenant."""
    carriers = (await db.execute(
        select(Carrier).where(Carrier.tenant_id == current_user.tenant_id, Carrier.is_active == True)
        .order_by(Carrier.name)
    )).scalars().all()
    return [_carrier_to_dict(c) for c in carriers]


@router.post("/carriers")
async def create_carrier(
    body: CarrierCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new carrier."""
    carrier = Carrier(
        tenant_id=current_user.tenant_id,
        name=body.name,
        contact_name=body.contact_name,
        contact_phone=body.contact_phone,
        contact_email=body.contact_email,
        api_endpoint=body.api_endpoint,
        capabilities=body.capabilities or {},
    )
    db.add(carrier)
    await db.commit()
    await db.refresh(carrier)
    return _carrier_to_dict(carrier)


# ═══════════════════════════════════════════════════════════════════════
# KPI / STATS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/stats")
async def logistics_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard KPI stats for logistics."""
    tid = current_user.tenant_id

    # Status counts
    status_counts = {}
    for s in ["created", "picked", "assigned", "pickup_confirmed", "in_transit",
              "at_hub", "out_for_delivery", "delivered", "failed_delivery", "damaged", "cancelled"]:
        count = (await db.execute(
            select(func.count()).where(Shipment.tenant_id == tid, Shipment.status == s)
        )).scalar() or 0
        status_counts[s] = count

    total = sum(status_counts.values())
    in_transit = status_counts.get("in_transit", 0) + status_counts.get("out_for_delivery", 0) + status_counts.get("at_hub", 0)
    delivered = status_counts.get("delivered", 0)
    delayed = status_counts.get("failed_delivery", 0) + status_counts.get("damaged", 0)

    # On-time delivery %
    on_time_pct = 0
    if delivered > 0:
        on_time = (await db.execute(
            select(func.count()).where(
                Shipment.tenant_id == tid,
                Shipment.status == "delivered",
                Shipment.actual_delivery <= Shipment.estimated_delivery,
            )
        )).scalar() or 0
        on_time_pct = round((on_time / delivered) * 100, 1)

    return {
        "total": total,
        "in_transit": in_transit,
        "delivered": delivered,
        "delayed": delayed,
        "pending": status_counts.get("created", 0) + status_counts.get("picked", 0) + status_counts.get("assigned", 0),
        "on_time_delivery_pct": on_time_pct,
        "status_breakdown": status_counts,
    }


# ═══════════════════════════════════════════════════════════════════════
# SMART EXTRACT — AI Vision Document Processing
# ═══════════════════════════════════════════════════════════════════════

LOGISTICS_EXTRACTION_PROMPT = """
You are an expert logistics data extraction AI.
Analyze this document image (Bill of Lading, Packing List, Delivery Receipt / POD, or Shipping Invoice).
Extract ALL visible data and return it ONLY as a valid JSON object. Do NOT include markdown formatting.

Return this exact JSON schema:
{
  "event_type": "created | picked_up_from_factory | delivered | damaged",
  "shipment_number": "extracted shipment/BL/AWB number if visible, else null",
  "origin": {"city": "", "country": "", "address": ""},
  "destination": {"city": "", "country": "", "address": ""},
  "goods_description": "human-readable summary of goods",
  "packages": [
    {"barcode": "if visible", "weight_kg": 0, "contents": "description of goods"}
  ],
  "total_weight_kg": 0,
  "incoterms": "FOB/CIF/EXW etc if visible, else null",
  "carrier_name": "carrier/shipping line name if visible",
  "customer_name": "consignee/receiver name if visible",
  "customer_phone": "consignee phone if visible",
  "pod": {
    "recipient_name": "who signed/received if this is a delivery receipt",
    "notes": "any delivery notes"
  },
  "notes": "vehicle number, driver name, damages observed, or any other info"
}

Rules:
- If it looks like a delivery receipt (POD), set event_type to "delivered"
- If it looks like a new packing list or BL, set event_type to "created"
- If damage is mentioned/visible, set event_type to "damaged"
- Extract actual product names (e.g. pistachios, dates, dry fruits, electronics)
- Use null for fields you cannot determine from the image
- Be precise with weights and quantities
"""


@router.post("/smart-extract")
async def smart_extract_document(
    file: UploadFile = File(...),
    auto_create: bool = Form(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI Vision extraction: upload a photo of a logistics document (BL, packing list, POD).
    The AI extracts structured data and optionally creates/updates a shipment automatically.
    """
    tenant_id = current_user.tenant_id

    # Validate file
    allowed = ["image/jpeg", "image/png", "image/webp", "image/heic", "application/pdf"]
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    logger.info(f"smart-extract: file={file.filename}, size={len(raw)}, type={file.content_type}")

    # Call Gemini Vision
    try:
        extracted = await _call_gemini_vision(raw, file.content_type or "image/jpeg")
    except Exception as e:
        logger.exception(f"smart-extract AI error: {e}")
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {str(e)}")

    result = {
        "success": True,
        "extracted": extracted,
        "shipment": None,
        "event": None,
    }

    # Auto-create shipment or add event
    if auto_create:
        event_type = extracted.get("event_type", "created")

        if event_type in ("created",):
            # Create new shipment from extracted data
            shipment = Shipment(
                tenant_id=tenant_id,
                shipment_number=extracted.get("shipment_number") or _generate_shipment_number(),
                origin=extracted.get("origin") or {},
                destination=extracted.get("destination") or {},
                goods_description=extracted.get("goods_description"),
                total_weight_kg=extracted.get("total_weight_kg"),
                incoterms=extracted.get("incoterms"),
                customer_name=extracted.get("customer_name"),
                customer_phone=extracted.get("customer_phone"),
                status="created",
                ai_extracted=True,
                ai_confidence=0.85,
            )
            db.add(shipment)
            await db.flush()

            # Add packages
            pkgs = extracted.get("packages") or []
            shipment.total_packages = len(pkgs)
            for pkg_data in pkgs:
                p = ShipmentPackage(
                    shipment_id=shipment.id,
                    barcode=pkg_data.get("barcode"),
                    weight_kg=pkg_data.get("weight_kg"),
                    contents=pkg_data.get("contents"),
                )
                db.add(p)

            # Create event
            ev = ShipmentEvent(
                shipment_id=shipment.id,
                event_type="created",
                actor=f"ai:vision",
                notes=extracted.get("notes"),
            )
            db.add(ev)
            await db.commit()
            await db.refresh(shipment)

            result["shipment"] = _shipment_to_dict(shipment)
            result["event"] = _event_to_dict(ev)

        elif event_type == "delivered":
            # Try to find existing shipment by number
            shp_num = extracted.get("shipment_number")
            shipment = None
            if shp_num:
                shipment = (await db.execute(
                    select(Shipment).where(
                        Shipment.tenant_id == tenant_id,
                        Shipment.shipment_number == shp_num,
                    )
                )).scalar_one_or_none()

            if shipment:
                shipment.status = "delivered"
                shipment.actual_delivery = datetime.datetime.utcnow()
                pod = extracted.get("pod") or {}
                shipment.pod_recipient_name = pod.get("recipient_name")

                ev = ShipmentEvent(
                    shipment_id=shipment.id,
                    event_type="delivered",
                    actor="ai:vision",
                    notes=extracted.get("notes") or pod.get("notes"),
                )
                db.add(ev)
                await db.commit()
                await db.refresh(shipment)

                result["shipment"] = _shipment_to_dict(shipment)
                result["event"] = _event_to_dict(ev)

                # Trigger WhatsApp notification
                try:
                    await _notify_delivery_whatsapp(shipment, extracted, db)
                except Exception as e:
                    logger.warning(f"WhatsApp notification failed: {e}")
            else:
                # No matching shipment found, create new one as delivered
                shipment = Shipment(
                    tenant_id=tenant_id,
                    shipment_number=shp_num or _generate_shipment_number(),
                    origin=extracted.get("origin") or {},
                    destination=extracted.get("destination") or {},
                    goods_description=extracted.get("goods_description"),
                    customer_name=extracted.get("customer_name"),
                    customer_phone=extracted.get("customer_phone"),
                    status="delivered",
                    actual_delivery=datetime.datetime.utcnow(),
                    ai_extracted=True,
                    ai_confidence=0.85,
                )
                db.add(shipment)
                await db.flush()
                ev = ShipmentEvent(
                    shipment_id=shipment.id,
                    event_type="delivered",
                    actor="ai:vision",
                    notes=extracted.get("notes"),
                )
                db.add(ev)
                await db.commit()
                await db.refresh(shipment)
                result["shipment"] = _shipment_to_dict(shipment)
                result["event"] = _event_to_dict(ev)

        elif event_type == "damaged":
            # Similar to delivered, find or create
            shp_num = extracted.get("shipment_number")
            shipment = None
            if shp_num:
                shipment = (await db.execute(
                    select(Shipment).where(
                        Shipment.tenant_id == tenant_id,
                        Shipment.shipment_number == shp_num,
                    )
                )).scalar_one_or_none()

            if shipment:
                shipment.status = "damaged"
                ev = ShipmentEvent(
                    shipment_id=shipment.id,
                    event_type="damaged",
                    actor="ai:vision",
                    notes=extracted.get("notes"),
                    payload={"damage_details": extracted.get("notes")},
                )
                db.add(ev)
                await db.commit()
                await db.refresh(shipment)
                result["shipment"] = _shipment_to_dict(shipment)
                result["event"] = _event_to_dict(ev)

    return result


# ─── Gemini Vision Call ──────────────────────────────────────────────

async def _call_gemini_vision(image_bytes: bytes, mime_type: str) -> dict:
    """Call Gemini Vision to extract logistics data from a document image."""
    import google.generativeai as genai
    import asyncio

    # Use key rotation from gemini_service if available
    api_key = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("No Gemini API key configured (GEMINI_API_KEY_1 or GEMINI_API_KEY)")

    genai.configure(api_key=api_key)

    image_part = {
        "mime_type": mime_type,
        "data": image_bytes,
    }

    model = genai.GenerativeModel("gemini-2.5-flash")

    def _sync_call():
        response = model.generate_content([LOGISTICS_EXTRACTION_PROMPT, image_part])
        return response.text

    response_text = await asyncio.to_thread(_sync_call)

    # Parse JSON from response
    import re
    # Try direct parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    # Try extracting from code block
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {"raw_response": response_text, "event_type": "created"}


# ─── WhatsApp Notification ───────────────────────────────────────────

async def _notify_delivery_whatsapp(shipment: Shipment, extracted: dict, db: AsyncSession):
    """Send WhatsApp notification on delivery via WAHA."""
    import httpx

    if not shipment.customer_phone:
        return

    waha_url = os.environ.get("WAHA_URL", "http://waha:3000")
    phone = shipment.customer_phone.replace("+", "").strip()
    if not phone.endswith("@c.us"):
        phone = f"{phone}@c.us"

    pod = extracted.get("pod") or {}
    goods = shipment.goods_description or "your shipment"
    recipient = pod.get("recipient_name") or "the receiver"

    message = (
        f"Hello {shipment.customer_name or 'Valued Customer'},\n\n"
        f"Your shipment {shipment.shipment_number} has been successfully delivered.\n\n"
        f"Goods: {goods}\n"
        f"Received by: {recipient}\n"
        f"Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"Thank you for your business!"
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"{waha_url}/api/sendText", json={
                "chatId": phone,
                "text": message,
                "session": "default",
            })
        shipment.notification_sent = True
        await db.commit()
        logger.info(f"WhatsApp delivery notification sent for {shipment.shipment_number}")
    except Exception as e:
        logger.warning(f"WAHA notification failed: {e}")


# ─── Serialization Helpers ───────────────────────────────────────────

def _shipment_to_dict(s: Shipment) -> dict:
    return {
        "id": str(s.id),
        "shipment_number": s.shipment_number,
        "order_id": s.order_id,
        "origin": s.origin or {},
        "destination": s.destination or {},
        "status": s.status,
        "carrier_id": str(s.carrier_id) if s.carrier_id else None,
        "goods_description": s.goods_description,
        "total_weight_kg": s.total_weight_kg,
        "total_packages": s.total_packages,
        "incoterms": s.incoterms,
        "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
        "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
        "customer_name": s.customer_name,
        "customer_phone": s.customer_phone,
        "ai_extracted": s.ai_extracted,
        "ai_confidence": s.ai_confidence,
        "notification_sent": s.notification_sent,
        "pod_recipient_name": s.pod_recipient_name,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _event_to_dict(e: ShipmentEvent) -> dict:
    return {
        "id": str(e.id),
        "shipment_id": str(e.shipment_id),
        "event_type": e.event_type,
        "actor": e.actor,
        "payload": e.payload or {},
        "latitude": e.latitude,
        "longitude": e.longitude,
        "location_name": e.location_name,
        "speed_kmh": e.speed_kmh,
        "eta": e.eta.isoformat() if e.eta else None,
        "notes": e.notes,
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
    }


def _package_to_dict(p: ShipmentPackage) -> dict:
    return {
        "id": str(p.id),
        "barcode": p.barcode,
        "weight_kg": p.weight_kg,
        "dimensions": p.dimensions,
        "contents": p.contents,
    }


def _carrier_to_dict(c: Carrier) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "contact_name": c.contact_name,
        "contact_phone": c.contact_phone,
        "contact_email": c.contact_email,
        "capabilities": c.capabilities or {},
        "is_active": c.is_active,
    }
