"""
WhatsApp Auto-Notifications — Pillar 3: WhatsApp-First Automation
Automatic beautiful WhatsApp notifications for business events.

Sends notifications for:
- Shipment status updates (with tracking timeline link)
- Delivery confirmations (with receipt image)
- Deal updates
- Invoice reminders
- Follow-up reminders
"""
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.waha_service import WAHAService

logger = logging.getLogger(__name__)


class WhatsAppNotificationTemplates:
    """Beautiful, multi-language WhatsApp message templates."""

    @staticmethod
    def shipment_update(
        tracking_number: str,
        status: str,
        origin: str = "",
        destination: str = "",
        eta: str = "",
        timeline_url: str = "",
        language: str = "fa",
    ) -> str:
        status_emoji = {
            "booked": "📋",
            "picked_up": "📦",
            "in_transit": "🚢",
            "customs_clearance": "🏛️",
            "out_for_delivery": "🚛",
            "delivered": "✅",
            "delayed": "⚠️",
        }.get(status, "📦")

        status_labels = {
            "fa": {
                "booked": "ثبت شد",
                "picked_up": "بارگیری شد",
                "in_transit": "در مسیر",
                "customs_clearance": "ترخیص گمرک",
                "out_for_delivery": "در حال تحویل",
                "delivered": "تحویل داده شد",
                "delayed": "تاخیر",
            },
            "en": {
                "booked": "Booked",
                "picked_up": "Picked Up",
                "in_transit": "In Transit",
                "customs_clearance": "Customs Clearance",
                "out_for_delivery": "Out for Delivery",
                "delivered": "Delivered",
                "delayed": "Delayed",
            },
            "ar": {
                "booked": "تم الحجز",
                "picked_up": "تم الاستلام",
                "in_transit": "في الطريق",
                "customs_clearance": "التخليص الجمركي",
                "out_for_delivery": "قيد التوصيل",
                "delivered": "تم التسليم",
                "delayed": "تأخير",
            },
        }

        labels = status_labels.get(language, status_labels["en"])
        status_text = labels.get(status, status)

        if language == "fa":
            msg = f"""{status_emoji} *بروزرسانی محموله*

📍 شماره پیگیری: `{tracking_number}`
🔄 وضعیت: *{status_text}*"""
            if origin and destination:
                msg += f"\n🌍 مسیر: {origin} → {destination}"
            if eta:
                msg += f"\n📅 زمان تخمینی رسیدن: {eta}"
            if timeline_url:
                msg += f"\n\n🔗 مشاهده تایم‌لاین: {timeline_url}"
            msg += "\n\n_آرتین اسمارت ترید — دستیار هوشمند تجارت شما_"

        elif language == "ar":
            msg = f"""{status_emoji} *تحديث الشحنة*

📍 رقم التتبع: `{tracking_number}`
🔄 الحالة: *{status_text}*"""
            if origin and destination:
                msg += f"\n🌍 المسار: {origin} → {destination}"
            if eta:
                msg += f"\n📅 الوصول المتوقع: {eta}"
            if timeline_url:
                msg += f"\n\n🔗 عرض الجدول الزمني: {timeline_url}"
            msg += "\n\n_آرتين سمارت تريد — مساعدك التجاري الذكي_"

        else:
            msg = f"""{status_emoji} *Shipment Update*

📍 Tracking: `{tracking_number}`
🔄 Status: *{status_text}*"""
            if origin and destination:
                msg += f"\n🌍 Route: {origin} → {destination}"
            if eta:
                msg += f"\n📅 ETA: {eta}"
            if timeline_url:
                msg += f"\n\n🔗 View Timeline: {timeline_url}"
            msg += "\n\n_Artin Smart Trade — Your AI Trade Assistant_"

        return msg

    @staticmethod
    def delivery_confirmation(
        tracking_number: str,
        delivered_to: str = "",
        delivery_time: str = "",
        language: str = "fa",
    ) -> str:
        if language == "fa":
            msg = f"""✅ *تایید تحویل*

📦 شماره پیگیری: `{tracking_number}`
👤 تحویل گیرنده: {delivered_to or 'N/A'}
🕐 زمان تحویل: {delivery_time or 'N/A'}

محموله شما با موفقیت تحویل داده شد.
اگر سوالی دارید، همینجا پیام دهید.

_آرتین اسمارت ترید_"""
        elif language == "ar":
            msg = f"""✅ *تأكيد التسليم*

📦 رقم التتبع: `{tracking_number}`
👤 المستلم: {delivered_to or 'N/A'}
🕐 وقت التسليم: {delivery_time or 'N/A'}

تم تسليم شحنتك بنجاح.
إذا كان لديك أي أسئلة، أرسل رسالة هنا.

_آرتين سمارت تريد_"""
        else:
            msg = f"""✅ *Delivery Confirmation*

📦 Tracking: `{tracking_number}`
👤 Delivered to: {delivered_to or 'N/A'}
🕐 Delivery time: {delivery_time or 'N/A'}

Your shipment has been delivered successfully.
If you have any questions, message here.

_Artin Smart Trade_"""
        return msg

    @staticmethod
    def deal_update(
        deal_title: str,
        stage: str,
        next_step: str = "",
        language: str = "fa",
    ) -> str:
        if language == "fa":
            msg = f"""💼 *بروزرسانی معامله*

📋 عنوان: *{deal_title}*
📊 مرحله: {stage}"""
            if next_step:
                msg += f"\n➡️ گام بعدی: {next_step}"
            msg += "\n\n_آرتین اسمارت ترید_"
        else:
            msg = f"""💼 *Deal Update*

📋 Title: *{deal_title}*
📊 Stage: {stage}"""
            if next_step:
                msg += f"\n➡️ Next step: {next_step}"
            msg += "\n\n_Artin Smart Trade_"
        return msg

    @staticmethod
    def approval_request(
        title: str,
        description: str = "",
        approval_url: str = "",
        language: str = "fa",
    ) -> str:
        if language == "fa":
            msg = f"""🤖 *تایید مورد نیاز*

📋 {title}"""
            if description:
                msg += f"\n📝 {description[:200]}"
            if approval_url:
                msg += f"\n\n🔗 بررسی و تایید: {approval_url}"
            msg += "\n\nلطفاً این اقدام را بررسی و تایید کنید."
            msg += "\n_آرتین اسمارت ترید_"
        else:
            msg = f"""🤖 *Approval Required*

📋 {title}"""
            if description:
                msg += f"\n📝 {description[:200]}"
            if approval_url:
                msg += f"\n\n🔗 Review & Approve: {approval_url}"
            msg += "\n\nPlease review and approve this action."
            msg += "\n_Artin Smart Trade_"
        return msg


class WhatsAppAutoNotifier:
    """
    Automatically sends WhatsApp notifications for business events.
    This is the bridge between backend events and customer communication.
    """

    @staticmethod
    async def notify_shipment_update(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        phone: str,
        tracking_number: str,
        status: str,
        origin: str = "",
        destination: str = "",
        eta: str = "",
        timeline_url: str = "",
        language: str = "fa",
    ) -> Dict[str, Any]:
        """Send shipment status update notification via WhatsApp."""
        try:
            message = WhatsAppNotificationTemplates.shipment_update(
                tracking_number=tracking_number,
                status=status,
                origin=origin,
                destination=destination,
                eta=eta,
                timeline_url=timeline_url,
                language=language,
            )
            result = await WAHAService.send_and_persist(
                db=db,
                tenant_id=tenant_id,
                phone=phone,
                text=message,
                event_type="shipment_notification",
            )
            return {"status": "sent", "message_id": str(result.id)}
        except Exception as e:
            logger.error(f"Failed to send shipment notification: {e}")
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def notify_delivery(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        phone: str,
        tracking_number: str,
        delivered_to: str = "",
        delivery_time: str = "",
        language: str = "fa",
    ) -> Dict[str, Any]:
        """Send delivery confirmation notification."""
        try:
            message = WhatsAppNotificationTemplates.delivery_confirmation(
                tracking_number=tracking_number,
                delivered_to=delivered_to,
                delivery_time=delivery_time,
                language=language,
            )
            result = await WAHAService.send_and_persist(
                db=db,
                tenant_id=tenant_id,
                phone=phone,
                text=message,
                event_type="delivery_confirmation",
            )
            return {"status": "sent", "message_id": str(result.id)}
        except Exception as e:
            logger.error(f"Failed to send delivery notification: {e}")
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def notify_approval_needed(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        phone: str,
        title: str,
        description: str = "",
        approval_url: str = "",
        language: str = "fa",
    ) -> Dict[str, Any]:
        """Send approval request notification to manager via WhatsApp."""
        try:
            message = WhatsAppNotificationTemplates.approval_request(
                title=title,
                description=description,
                approval_url=approval_url,
                language=language,
            )
            result = await WAHAService.send_and_persist(
                db=db,
                tenant_id=tenant_id,
                phone=phone,
                text=message,
                event_type="approval_request",
            )
            return {"status": "sent", "message_id": str(result.id)}
        except Exception as e:
            logger.error(f"Failed to send approval notification: {e}")
            return {"status": "failed", "error": str(e)}
