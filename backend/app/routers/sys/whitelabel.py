"""
/sys/whitelabel — Domain management and activation.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.phase6 import SystemAdmin, WhitelabelDomain, WhitelabelConfig
from app.services.sys_admin_auth import get_current_sys_admin, write_sys_audit

router = APIRouter()


@router.get("/domains", summary="List All Whitelabel Domain Requests")
def list_domains(db: Session = Depends(get_db), admin: SystemAdmin = Depends(get_current_sys_admin)):
    domains = db.query(WhitelabelDomain).order_by(WhitelabelDomain.created_at.desc()).all()
    return [
        {
            "id": str(d.id),
            "tenant_id": str(d.tenant_id),
            "domain": d.domain,
            "status": d.status,
            "verification_token": d.verification_token,
            "verified_at": d.verified_at.isoformat() if d.verified_at else None,
        }
        for d in domains
    ]


@router.post("/domains/{domain_id}/activate", summary="Manually Activate Domain")
def activate_domain(
    domain_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    domain = db.query(WhitelabelDomain).filter(WhitelabelDomain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    before = {"status": domain.status}
    domain.status = "active"
    domain.verified_at = datetime.utcnow()
    db.commit()

    write_sys_audit(
        db, action="domain_activate", resource_type="whitelabel_domain",
        actor_sys_admin_id=admin.id, tenant_id=domain.tenant_id,
        resource_id=str(domain_id),
        before_state=before, after_state={"status": "active"},
        ip_address=request.client.host if request.client else None,
    )
    return {"status": "active", "domain": domain.domain, "domain_id": str(domain_id)}


@router.post("/domains/{domain_id}/disable", summary="Disable Domain")
def disable_domain(
    domain_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    domain = db.query(WhitelabelDomain).filter(WhitelabelDomain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    before = {"status": domain.status}
    domain.status = "disabled"
    db.commit()
    write_sys_audit(db, action="domain_disable", resource_type="whitelabel_domain",
                    actor_sys_admin_id=admin.id, tenant_id=domain.tenant_id,
                    resource_id=str(domain_id), before_state=before,
                    after_state={"status": "disabled"})
    return {"status": "disabled", "domain_id": str(domain_id)}
