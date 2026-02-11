from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from uuid import UUID
import uuid
from datetime import datetime, timedelta
import logging

from app.models.followup import CRMFollowUpExecution, CRMFollowUpRule, CRMRevenueAttribution
from app.models.crm import CRMConversation, CRMContact, CRMDeal
from app.models.whatsapp import WhatsAppMessage
from app.services.whatsapp import WhatsAppService
from app.services.billing import BillingService

logger = logging.getLogger(__name__)

class FollowUpService:
    @staticmethod
    def create_rule(db: Session, tenant_id: UUID, name: str, template: str, delay_minutes: int) -> CRMFollowUpRule:
        rule = CRMFollowUpRule(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            template_body=template,
            delay_minutes=delay_minutes
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def schedule_followup(db: Session, tenant_id: UUID, contact_id: UUID, conversation_id: UUID, rule_id: UUID, campaign_id: UUID = None):
        """
        Schedule a follow-up execution based on a rule.
        """
        rule = db.execute(select(CRMFollowUpRule).where(CRMFollowUpRule.id == rule_id)).scalar_one_or_none()
        if not rule or not rule.is_active:
            return

        scheduled_at = datetime.utcnow() + timedelta(minutes=rule.delay_minutes)
        
        execution = CRMFollowUpExecution(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            rule_id=rule.id,
            contact_id=contact_id,
            conversation_id=conversation_id,
            campaign_id=campaign_id,
            scheduled_at=scheduled_at,
            status="scheduled",
            attempt=1
        )
        db.add(execution)
        db.commit()
        return execution

    @staticmethod
    def cancel_pending_followups(db: Session, conversation_id: UUID):
        """
        Cancel any pending follow-ups for this conversation (e.g. user replied).
        """
        executions = db.execute(
            select(CRMFollowUpExecution)
            .where(CRMFollowUpExecution.conversation_id == conversation_id)
            .where(CRMFollowUpExecution.status == "scheduled")
        ).scalars().all()
        
        for exe in executions:
            exe.status = "cancelled"
        
        if executions:
            db.commit()
            logger.info(f"Cancelled {len(executions)} followups for conversation {conversation_id}")

    @staticmethod
    def process_due_followups():
        """
        Check for pending follow-ups that are due.
        This runs in a background loop/scheduler.
        """
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            due_executions = db.execute(
                select(CRMFollowUpExecution)
                .where(CRMFollowUpExecution.status == "scheduled")
                .where(CRMFollowUpExecution.scheduled_at <= now)
            ).scalars().all()
            
            for exe in due_executions:
                try:
                    # Double check: Has user replied since schedule?
                    conv = db.execute(select(CRMConversation).where(CRMConversation.id == exe.conversation_id)).scalar_one()
                    
                    last_msg = db.execute(
                        select(WhatsAppMessage)
                        .where(WhatsAppMessage.conversation_id == conv.id)
                        .order_by(WhatsAppMessage.created_at.desc())
                        .limit(1)
                    ).scalar_one_or_none()
                    
                    if last_msg and last_msg.direction == "inbound":
                        exe.status = "cancelled"
                        exe.error = "User replied"
                        db.commit()
                        continue
                        
                    # Send Follow-Up
                    rule = db.execute(select(CRMFollowUpRule).where(CRMFollowUpRule.id == exe.rule_id)).scalar_one()
                    contact = db.execute(select(CRMContact).where(CRMContact.id == exe.contact_id)).scalar_one()
                    
                    body = rule.template_body.replace("{{first_name}}", contact.first_name)
                    
                    # Deduct & Send
                    cost = 0.5
                    BillingService.deduct_balance(db, exe.tenant_id, cost, f"Follow-up: {rule.name}")
                    
                    try:
                        wamid = WhatsAppService.send_template(contact.phone, "followup_template", {"text": body})
                    except Exception as send_err:
                        # REFUND on send failure
                        BillingService.refund(db, exe.tenant_id, cost, f"Refund follow-up send failure: {rule.name}")
                        exe.status = "failed"
                        exe.error = f"Send failed: {str(send_err)}"
                        db.commit()
                        logger.error(f"Follow-up send failed for {contact.phone}: {send_err}")
                        continue
                    
                    # Log Message
                    wa_msg = WhatsAppMessage(
                        tenant_id=exe.tenant_id,
                        recipient_phone=contact.phone,
                        content=body,
                        status="sent",
                        message_id=wamid,
                        cost=cost,
                        direction="outbound",
                        conversation_id=conv.id
                    )
                    db.add(wa_msg)
                    
                    # Update Conversation
                    conv.last_message_at = datetime.utcnow()
                    
                    # Mark Done
                    exe.status = "sent"
                    exe.sent_at = datetime.utcnow()
                    
                    # Reschedule Logic (Multi-attempt)
                    if exe.attempt < rule.max_attempts:
                        new_schedule = datetime.utcnow() + timedelta(minutes=rule.delay_minutes)
                        new_exe = CRMFollowUpExecution(
                            id=uuid.uuid4(),
                            tenant_id=exe.tenant_id,
                            rule_id=rule.id,
                            contact_id=exe.contact_id,
                            conversation_id=exe.conversation_id,
                            campaign_id=exe.campaign_id,
                            status="scheduled",
                            scheduled_at=new_schedule,
                            attempt=exe.attempt + 1
                        )
                        db.add(new_exe)
                    
                    db.commit()
                    logger.info(f"Executed follow-up {exe.id} for {contact.phone}")
                    
                except Exception as e:
                    logger.error(f"Failed follow-up {exe.id}: {e}")
                    exe.status = "failed"
                    exe.error = str(e)
                    db.commit()
                    
        finally:
            db.close()

    @staticmethod
    def attribute_revenue(db: Session, deal_id: UUID):
        """
        Attribute revenue to the last touch (campaign/followup).
        """
        deal = db.execute(select(CRMDeal).where(CRMDeal.id == deal_id)).scalar_one_or_none()
        if not deal or deal.status != "won" or not deal.contact_id:
            return

        # Find last outbound message to this contact
        contact = db.execute(select(CRMContact).where(CRMContact.id == deal.contact_id)).scalar_one()
        
        last_msg = db.execute(
            select(WhatsAppMessage)
            .where(WhatsAppMessage.recipient_phone == contact.phone)
            .where(WhatsAppMessage.direction == "outbound")
            .order_by(WhatsAppMessage.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        if last_msg:
            # Check if this message was from a campaign or follow-up
            # Note: WA message doesn't store campaign_id directly unless we add it or link via conversation/execution.
            # We can check crm_campaign_messages or crm_followup_executions by whatsapp_message_id (if we added column)
            # Short-term: Just link via time proximity or explicit link if available.
            
            # Since we don't strictly link WA message to Campaign in WA table (only in crm_campaign_messages), 
            # we can try to find the campaign message.
            
            # Simple approach: Create Attribution entry pointing to message_id
            attribution = CRMRevenueAttribution(
                id=uuid.uuid4(),
                tenant_id=deal.tenant_id,
                deal_id=deal.id,
                message_id=last_msg.message_id,
                attribution_type="last_touch",
                amount=deal.value or 0
            )
            db.add(attribution)
            db.commit()

import asyncio

async def start_followup_scheduler():
    """
    Simple background loop to check for due follow-ups every 60 seconds.
    """
    logger.info("Starting Follow-Up Scheduler...")
    while True:
        try:
            await asyncio.to_thread(FollowUpService.process_due_followups)
        except Exception as e:
            logger.error(f"Follow-Up Scheduler Error: {e}")
        
        await asyncio.sleep(60)
