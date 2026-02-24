from sqlalchemy.ext.asyncio import AsyncSession
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
    async def create_rule(db: AsyncSession, tenant_id: UUID, name: str, template: str, delay_minutes: int) -> CRMFollowUpRule:
        rule = CRMFollowUpRule(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            template_body=template,
            delay_minutes=delay_minutes
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def schedule_followup(db: AsyncSession, tenant_id: UUID, contact_id: UUID, conversation_id: UUID, rule_id: UUID, campaign_id: UUID = None):
        """
        Schedule a follow-up execution based on a rule.
        """
        res = await db.execute(select(CRMFollowUpRule).where(CRMFollowUpRule.id == rule_id))
        rule = res.scalar_one_or_none()
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
        await db.commit()
        return execution

    @staticmethod
    async def cancel_pending_followups(db: AsyncSession, conversation_id: UUID):
        """
        Cancel any pending follow-ups for this conversation (e.g. user replied).
        """
        res = await db.execute(
            select(CRMFollowUpExecution)
            .where(CRMFollowUpExecution.conversation_id == conversation_id)
            .where(CRMFollowUpExecution.status == "scheduled")
        )
        executions = res.scalars().all()
        
        for exe in executions:
            exe.status = "cancelled"
        
        if executions:
            await db.commit()
            logger.info(f"Cancelled {len(executions)} followups for conversation {conversation_id}")

    @staticmethod
    async def process_due_followups():
        """
        Check for pending follow-ups that are due.
        This runs in a background loop/scheduler.
        """
        from app.db.session import AsyncSessionLocal as async_session_maker
        async with async_session_maker() as db:
            try:
                now = datetime.utcnow()
                res = await db.execute(
                    select(CRMFollowUpExecution)
                    .where(CRMFollowUpExecution.status == "scheduled")
                    .where(CRMFollowUpExecution.scheduled_at <= now)
                )
                due_executions = res.scalars().all()
                
                for exe in due_executions:
                    try:
                        # Double check: Has user replied since schedule?
                        c_res = await db.execute(select(CRMConversation).where(CRMConversation.id == exe.conversation_id))
                        conv = c_res.scalar_one()
                        
                        m_res = await db.execute(
                            select(WhatsAppMessage)
                            .where(WhatsAppMessage.conversation_id == conv.id)
                            .order_by(WhatsAppMessage.created_at.desc())
                            .limit(1)
                        )
                        last_msg = m_res.scalar_one_or_none()
                        
                        if last_msg and last_msg.direction == "inbound":
                            exe.status = "cancelled"
                            exe.error = "User replied"
                            await db.commit()
                            continue
                            
                        # Send Follow-Up
                        r_res = await db.execute(select(CRMFollowUpRule).where(CRMFollowUpRule.id == exe.rule_id))
                        rule = r_res.scalar_one()
                        
                        ct_res = await db.execute(select(CRMContact).where(CRMContact.id == exe.contact_id))
                        contact = ct_res.scalar_one()
                        
                        body = rule.template_body.replace("{{first_name}}", contact.first_name)
                        
                        # Deduct & Send
                        cost = 0.5
                        async with db.begin_nested():
                            await BillingService.deduct_balance(db, exe.tenant_id, cost, f"Follow-up: {rule.name}")
                        
                        try:
                            wamid = await WhatsAppService.send_template(contact.phone, "followup_template", {"text": body})
                        except Exception as send_err:
                            # REFUND on send failure
                            async with db.begin_nested():
                                await BillingService.refund(db, exe.tenant_id, cost, f"Refund follow-up send failure: {rule.name}")
                            exe.status = "failed"
                            exe.error = f"Send failed: {str(send_err)}"
                            await db.commit()
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
                        
                        await db.commit()
                        logger.info(f"Executed follow-up {exe.id} for {contact.phone}")
                        
                    except Exception as e:
                        logger.error(f"Failed follow-up {exe.id}: {e}")
                        exe.status = "failed"
                        exe.error = str(e)
                        await db.commit()
            except Exception as e:
                logger.error(f"Follow-Up Service Global Error: {e}")

    @staticmethod
    async def attribute_revenue(db: AsyncSession, deal_id: UUID):
        """
        Attribute revenue to the last touch (campaign/followup).
        """
        d_res = await db.execute(select(CRMDeal).where(CRMDeal.id == deal_id))
        deal = d_res.scalar_one_or_none()
        if not deal or deal.status != "won" or not deal.contact_id:
            return

        ct_res = await db.execute(select(CRMContact).where(CRMContact.id == deal.contact_id))
        contact = ct_res.scalar_one()
        
        m_res = await db.execute(
            select(WhatsAppMessage)
            .where(WhatsAppMessage.recipient_phone == contact.phone)
            .where(WhatsAppMessage.direction == "outbound")
            .order_by(WhatsAppMessage.created_at.desc())
            .limit(1)
        )
        last_msg = m_res.scalar_one_or_none()
        
        if last_msg:
            attribution = CRMRevenueAttribution(
                id=uuid.uuid4(),
                tenant_id=deal.tenant_id,
                deal_id=deal.id,
                message_id=last_msg.message_id,
                attribution_type="last_touch",
                amount=deal.value or 0
            )
            db.add(attribution)
            await db.commit()

import asyncio

async def start_followup_scheduler():
    """
    Simple background loop to check for due follow-ups every 60 seconds.
    """
    logger.info("Starting Async Follow-Up Scheduler...")
    while True:
        try:
            await FollowUpService.process_due_followups()
        except Exception as e:
            logger.error(f"Follow-Up Scheduler Error: {e}")
        
        await asyncio.sleep(60)
