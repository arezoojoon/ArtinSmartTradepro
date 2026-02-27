"""
Control Tower Service — Pillar 2: Money-Making Engine
Smart alerts, actionable insights, and decision support for traders.

Instead of boring charts, the Control Tower provides:
- Real-time actionable alerts (shipment delays, price opportunities, etc.)
- AI-powered recommendations with one-click actions
- Smart notifications that drive revenue
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.orm import selectinload

from app.models.logistics import Shipment, ShipmentEvent, ShipmentStatus
from app.models.crm import CRMCompany, CRMContact, CRMDeal
from app.models.deal import Deal
from app.models.ai_approval import AIApprovalQueue, ApprovalStatus

logger = logging.getLogger(__name__)


class AlertSeverity:
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    OPPORTUNITY = "opportunity"


class AlertType:
    SHIPMENT_DELAY = "shipment_delay"
    SHIPMENT_ARRIVED = "shipment_arrived"
    DEAL_STALE = "deal_stale"
    LEAD_HOT = "lead_hot"
    PRICE_OPPORTUNITY = "price_opportunity"
    APPROVAL_PENDING = "approval_pending"
    FOLLOWUP_DUE = "followup_due"
    PAYMENT_OVERDUE = "payment_overdue"
    CUSTOMER_INACTIVE = "customer_inactive"
    INVENTORY_LOW = "inventory_low"


class ControlTowerService:
    """
    Generates actionable alerts and insights for the trader's dashboard.
    Each alert has a suggested action and a one-click execution path.
    """

    @staticmethod
    async def get_dashboard_alerts(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all active alerts for the Control Tower dashboard.
        Returns prioritized, actionable alerts.
        """
        alerts = []

        # 1. Shipment Alerts
        shipment_alerts = await ControlTowerService._get_shipment_alerts(db, tenant_id)
        alerts.extend(shipment_alerts)

        # 2. Deal/Pipeline Alerts
        deal_alerts = await ControlTowerService._get_deal_alerts(db, tenant_id)
        alerts.extend(deal_alerts)

        # 3. Pending Approval Alerts
        approval_alerts = await ControlTowerService._get_approval_alerts(db, tenant_id)
        alerts.extend(approval_alerts)

        # 4. Follow-up Alerts
        followup_alerts = await ControlTowerService._get_followup_alerts(db, tenant_id)
        alerts.extend(followup_alerts)

        # Sort by priority: critical > warning > opportunity > info
        priority_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.OPPORTUNITY: 2,
            AlertSeverity.INFO: 3,
        }
        alerts.sort(key=lambda a: (priority_order.get(a["severity"], 99), a.get("created_at", "")))

        return alerts[:limit]

    @staticmethod
    async def get_kpi_summary(
        db: AsyncSession,
        tenant_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get real-time KPI summary for Control Tower."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        # Active shipments
        active_shipments_q = await db.execute(
            select(func.count(Shipment.id)).where(
                Shipment.tenant_id == tenant_id,
                Shipment.status.notin_(["delivered", "cancelled"])
            )
        )
        active_shipments = active_shipments_q.scalar() or 0

        # Pending approvals
        pending_approvals_q = await db.execute(
            select(func.count(AIApprovalQueue.id)).where(
                AIApprovalQueue.tenant_id == tenant_id,
                AIApprovalQueue.status == ApprovalStatus.PENDING.value
            )
        )
        pending_approvals = pending_approvals_q.scalar() or 0

        # Active deals
        try:
            active_deals_q = await db.execute(
                select(func.count(CRMDeal.id)).where(
                    CRMDeal.tenant_id == tenant_id,
                    CRMDeal.stage.notin_(["closed_won", "closed_lost"])
                )
            )
            active_deals = active_deals_q.scalar() or 0
        except Exception:
            active_deals = 0

        # Total contacts
        try:
            contacts_q = await db.execute(
                select(func.count(CRMContact.id)).where(
                    CRMContact.tenant_id == tenant_id
                )
            )
            total_contacts = contacts_q.scalar() or 0
        except Exception:
            total_contacts = 0

        return {
            "active_shipments": active_shipments,
            "pending_approvals": pending_approvals,
            "active_deals": active_deals,
            "total_contacts": total_contacts,
            "last_updated": now.isoformat(),
        }

    @staticmethod
    async def _get_shipment_alerts(
        db: AsyncSession, tenant_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Generate shipment-related alerts."""
        alerts = []
        now = datetime.utcnow()

        try:
            # Delayed shipments (ETA passed but not delivered)
            delayed_q = await db.execute(
                select(Shipment).where(
                    Shipment.tenant_id == tenant_id,
                    Shipment.status.notin_(["delivered", "cancelled"]),
                    Shipment.eta < now
                ).limit(10)
            )
            delayed = delayed_q.scalars().all()

            for ship in delayed:
                days_late = (now - ship.eta).days if ship.eta else 0
                alerts.append({
                    "id": f"ship_delay_{ship.id}",
                    "type": AlertType.SHIPMENT_DELAY,
                    "severity": AlertSeverity.CRITICAL if days_late > 3 else AlertSeverity.WARNING,
                    "title_fa": f"⚠️ محموله {ship.tracking_number or 'N/A'} با {days_late} روز تاخیر",
                    "title_en": f"⚠️ Shipment {ship.tracking_number or 'N/A'} is {days_late} days late",
                    "description_fa": f"مقصد: {getattr(ship, 'destination', 'N/A')} — وضعیت: {ship.status}",
                    "description_en": f"Destination: {getattr(ship, 'destination', 'N/A')} — Status: {ship.status}",
                    "entity_id": str(ship.id),
                    "entity_type": "shipment",
                    "suggested_action": "notify_customer",
                    "action_label_fa": "به مشتری اطلاع بده",
                    "action_label_en": "Notify Customer",
                    "action_payload": {
                        "shipment_id": str(ship.id),
                        "action": "send_delay_notification",
                        "days_late": days_late,
                    },
                    "created_at": now.isoformat(),
                })

            # Recently arrived shipments
            recent_q = await db.execute(
                select(Shipment).where(
                    Shipment.tenant_id == tenant_id,
                    Shipment.status == "delivered",
                    Shipment.updated_at > (now - timedelta(hours=24))
                ).limit(5)
            )
            recent = recent_q.scalars().all()

            for ship in recent:
                alerts.append({
                    "id": f"ship_arrived_{ship.id}",
                    "type": AlertType.SHIPMENT_ARRIVED,
                    "severity": AlertSeverity.INFO,
                    "title_fa": f"✅ محموله {ship.tracking_number or 'N/A'} تحویل داده شد",
                    "title_en": f"✅ Shipment {ship.tracking_number or 'N/A'} delivered",
                    "description_fa": "تحویل با موفقیت انجام شد",
                    "description_en": "Delivery completed successfully",
                    "entity_id": str(ship.id),
                    "entity_type": "shipment",
                    "suggested_action": "confirm_delivery",
                    "action_label_fa": "تایید و ارسال رسید",
                    "action_label_en": "Confirm & Send Receipt",
                    "action_payload": {
                        "shipment_id": str(ship.id),
                        "action": "confirm_and_notify",
                    },
                    "created_at": now.isoformat(),
                })

        except Exception as e:
            logger.warning(f"Error getting shipment alerts: {e}")

        return alerts

    @staticmethod
    async def _get_deal_alerts(
        db: AsyncSession, tenant_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Generate deal pipeline alerts."""
        alerts = []
        now = datetime.utcnow()

        try:
            # Stale deals (no activity in 7+ days)
            stale_q = await db.execute(
                select(CRMDeal).where(
                    CRMDeal.tenant_id == tenant_id,
                    CRMDeal.stage.notin_(["closed_won", "closed_lost"]),
                    CRMDeal.updated_at < (now - timedelta(days=7))
                ).limit(10)
            )
            stale_deals = stale_q.scalars().all()

            for deal in stale_deals:
                days_stale = (now - deal.updated_at).days if deal.updated_at else 0
                alerts.append({
                    "id": f"deal_stale_{deal.id}",
                    "type": AlertType.DEAL_STALE,
                    "severity": AlertSeverity.WARNING,
                    "title_fa": f"💤 معامله «{deal.title or 'بدون نام'}» {days_stale} روز بدون فعالیت",
                    "title_en": f"💤 Deal '{deal.title or 'Untitled'}' inactive for {days_stale} days",
                    "description_fa": f"مرحله: {deal.stage} — ارزش: {deal.value or 'N/A'}",
                    "description_en": f"Stage: {deal.stage} — Value: {deal.value or 'N/A'}",
                    "entity_id": str(deal.id),
                    "entity_type": "deal",
                    "suggested_action": "send_followup",
                    "action_label_fa": "پیگیری بفرست",
                    "action_label_en": "Send Follow-up",
                    "action_payload": {
                        "deal_id": str(deal.id),
                        "action": "auto_followup",
                    },
                    "created_at": now.isoformat(),
                })

        except Exception as e:
            logger.warning(f"Error getting deal alerts: {e}")

        return alerts

    @staticmethod
    async def _get_approval_alerts(
        db: AsyncSession, tenant_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Generate pending approval alerts."""
        alerts = []
        now = datetime.utcnow()

        try:
            pending_q = await db.execute(
                select(AIApprovalQueue).where(
                    AIApprovalQueue.tenant_id == tenant_id,
                    AIApprovalQueue.status == ApprovalStatus.PENDING.value,
                ).order_by(desc(AIApprovalQueue.created_at)).limit(10)
            )
            pending = pending_q.scalars().all()

            for item in pending:
                alerts.append({
                    "id": f"approval_{item.id}",
                    "type": AlertType.APPROVAL_PENDING,
                    "severity": AlertSeverity.WARNING if item.priority == "high" else AlertSeverity.INFO,
                    "title_fa": f"🤖 تایید مورد نیاز: {item.title}",
                    "title_en": f"🤖 Approval needed: {item.title}",
                    "description_fa": item.description[:200] if item.description else "",
                    "description_en": item.description[:200] if item.description else "",
                    "entity_id": str(item.id),
                    "entity_type": "approval",
                    "suggested_action": "review_approval",
                    "action_label_fa": "بررسی و تایید",
                    "action_label_en": "Review & Approve",
                    "action_payload": {
                        "approval_id": str(item.id),
                        "action": "review",
                    },
                    "ai_confidence": item.ai_confidence,
                    "created_at": item.created_at.isoformat() if item.created_at else now.isoformat(),
                })

        except Exception as e:
            logger.warning(f"Error getting approval alerts: {e}")

        return alerts

    @staticmethod
    async def _get_followup_alerts(
        db: AsyncSession, tenant_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Generate follow-up reminder alerts."""
        alerts = []
        now = datetime.utcnow()

        try:
            # Contacts with no recent interaction
            inactive_q = await db.execute(
                select(CRMContact).where(
                    CRMContact.tenant_id == tenant_id,
                    CRMContact.updated_at < (now - timedelta(days=14))
                ).limit(5)
            )
            inactive = inactive_q.scalars().all()

            for contact in inactive:
                days_since = (now - contact.updated_at).days if contact.updated_at else 0
                alerts.append({
                    "id": f"followup_{contact.id}",
                    "type": AlertType.CUSTOMER_INACTIVE,
                    "severity": AlertSeverity.INFO,
                    "title_fa": f"📞 {contact.name or 'مخاطب'} — {days_since} روز بدون تماس",
                    "title_en": f"📞 {contact.name or 'Contact'} — {days_since} days no contact",
                    "description_fa": f"شرکت: {getattr(contact, 'company_name', 'N/A')}",
                    "description_en": f"Company: {getattr(contact, 'company_name', 'N/A')}",
                    "entity_id": str(contact.id),
                    "entity_type": "contact",
                    "suggested_action": "send_whatsapp",
                    "action_label_fa": "پیام واتساپ بفرست",
                    "action_label_en": "Send WhatsApp",
                    "action_payload": {
                        "contact_id": str(contact.id),
                        "action": "whatsapp_followup",
                    },
                    "created_at": now.isoformat(),
                })

        except Exception as e:
            logger.warning(f"Error getting followup alerts: {e}")

        return alerts
