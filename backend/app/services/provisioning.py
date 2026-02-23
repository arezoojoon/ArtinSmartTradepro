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
    async def run_for_tenant(db: Session, tenant_id: UUID, max_retries: int = 3):
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
            logger.info(f"Provisioning already complete for tenant {tenant_id}")
            return

        status.overall_status = ProvisioningState.RUNNING
        db.commit()

        # Step A: CRM Seeding (Idempotent)
        if status.crm_status != ProvisioningState.READY:
            try:
                status.crm_status = ProvisioningState.RUNNING
                db.commit()
                await seed_new_tenant(db, tenant_id)
                status.crm_status = ProvisioningState.READY
            except Exception as e:
                logger.error(f"CRM provisioning failed for {tenant_id}: {e}")
                status.crm_status = ProvisioningState.FAILED
                status.last_error = f"CRM Error: {str(e)}"
            db.commit()

        # Step B: WAHA Session Initialization (with Retries)
        if status.waha_status != ProvisioningState.READY:
            for attempt in range(max_retries):
                try:
                    status.waha_status = ProvisioningState.RUNNING
                    db.commit()
                    
                    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
                    session_name = f"tenant_{tenant.slug if tenant else tenant_id}"
                    
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        headers = {"X-Api-Key": WAHA_API_KEY} if WAHA_API_KEY else {}
                        resp = await client.post(
                            f"{WAHA_API_URL}/api/sessions",
                            json={"name": session_name, "start": True},
                            headers=headers
                        )
                        if resp.status_code not in (200, 201, 409):
                            resp.raise_for_status()
                    
                    status.waha_session_name = session_name
                    status.waha_status = ProvisioningState.READY
                    status.last_error = None
                    break # Success
                except Exception as e:
                    status.retry_count += 1
                    status.last_error = f"WAHA Attempt {attempt+1} failed: {str(e)}"
                    logger.warning(status.last_error)
                    db.commit()
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt) # Exponential backoff
                    else:
                        status.waha_status = ProvisioningState.FAILED

            db.commit()

        # Step C: Managed Telegram (Instant)
        if status.telegram_status != ProvisioningState.READY:
            status.telegram_status = ProvisioningState.READY
            status.telegram_deeplink = f"https://t.me/ArtinSmartBot?start={tenant_id}"
            db.commit()

        # Finalize Overall Status
        if status.crm_status == ProvisioningState.READY and status.waha_status == ProvisioningState.READY:
            status.overall_status = ProvisioningState.READY
            print(f"[PROVISIONING] ✅ Tenant {tenant_id} is READY")
        else:
            status.overall_status = ProvisioningState.PARTIAL
            print(f"[PROVISIONING] ⚠️ Tenant {tenant_id} is PARTIAL")
        
        db.commit()

async def trigger_provisioning(tenant_id: UUID):
    """ Enqueue provisioning logic. """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        service = ProvisioningService()
        await service.run_for_tenant(db, tenant_id)
    except Exception as e:
        logger.error(f"Fatal error in trigger_provisioning: {e}")
    finally:
        db.close()
