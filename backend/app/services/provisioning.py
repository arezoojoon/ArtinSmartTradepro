import logging
import asyncio
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.billing_ext import ProvisioningStatus, ProvisioningState
from app.models.tenant import Tenant
from app.services.tenant_seeder import seed_new_tenant
from app.services.waha_service import WAHAService, WAHA_API_URL, WAHA_API_KEY
import httpx

logger = logging.getLogger(__name__)

class ProvisioningService:
    @staticmethod
    async def run_for_tenant(db: Session, tenant_id: UUID):
        """
        Main entry point for provisioning a tenant's resources.
        Idempotent: checks status before running each step.
        """
        # 1. Ensure ProvisioningStatus record exists
        status = db.execute(
            select(ProvisioningStatus).where(ProvisioningStatus.tenant_id == tenant_id)
        ).scalar_one_or_none()

        if not status:
            status = ProvisioningStatus(tenant_id=tenant_id, overall_status=ProvisioningState.RUNNING)
            db.add(status)
            db.commit()
            db.refresh(status)

        if status.overall_status == ProvisioningState.READY:
            return # Already done

        status.overall_status = ProvisioningState.RUNNING
        db.commit()

        try:
            # Step A: CRM Seeding (Idempotent)
            if status.crm_status != ProvisioningState.READY:
                status.crm_status = ProvisioningState.RUNNING
                db.commit()
                # seed_new_tenant handles roles/pipelines.
                # Note: We use a wrapper or modified version if needed for idempotency.
                await seed_new_tenant(db, tenant_id)
                status.crm_status = ProvisioningState.READY
                db.commit()

            # Step B: WAHA Session Initialization
            if status.waha_status != ProvisioningState.READY:
                status.waha_status = ProvisioningState.RUNNING
                db.commit()
                
                tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
                session_name = f"tenant_{tenant.slug if tenant else tenant_id}"
                
                try:
                    # Call WAHA to create session
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        headers = {"X-Api-Key": WAHA_API_KEY} if WAHA_API_KEY else {}
                        # Just a placeholder for actual WAHA session creation endpoint
                        # WAHA usually auto-creates on first use or has a specific /sessions endpoint
                        resp = await client.post(
                            f"{WAHA_API_URL}/api/sessions",
                            json={"name": session_name, "start": True},
                            headers=headers
                        )
                        # 409 means already exists, which is fine
                        if resp.status_code not in (200, 201, 409):
                            resp.raise_for_status()
                    
                    status.waha_session_name = session_name
                    status.waha_status = ProvisioningState.READY
                except Exception as e:
                    logger.error(f"WAHA provisioning failed for {tenant_id}: {e}")
                    status.waha_status = ProvisioningState.FAILED
                    status.last_error = f"WAHA Error: {str(e)}"
                db.commit()

            # Step C: Managed Telegram Stub
            if status.telegram_status != ProvisioningState.READY:
                status.telegram_status = ProvisioningState.READY # Managed bot is instant
                status.telegram_deeplink = f"https://t.me/ArtinSmartBot?start={tenant_id}"
                db.commit()

            # Finalize
            if status.crm_status == ProvisioningState.READY and status.waha_status == ProvisioningState.READY:
                status.overall_status = ProvisioningState.READY
            else:
                status.overall_status = ProvisioningState.PARTIAL
            
            db.commit()

        except Exception as e:
            logger.exception(f"Provisioning failed for tenant {tenant_id}")
            status.overall_status = ProvisioningState.FAILED
            status.last_error = str(e)
            db.commit()

async def trigger_provisioning(tenant_id: UUID):
    """
    Wrapper to trigger provisioning in a background task.
    In a real app, this would enqueue a Celery task.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        service = ProvisioningService()
        await service.run_for_tenant(db, tenant_id)
    finally:
        db.close()
