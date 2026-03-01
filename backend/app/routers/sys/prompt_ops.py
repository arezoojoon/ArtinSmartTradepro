"""
/sys/prompts — Prompt Ops registry: families, versions, approval/deprecation, run logs.
"""
from uuid import UUID
from typing import Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phase6 import SystemAdmin, PromptFamily, PromptVersion, PromptRun
from app.services.sys_admin_auth import get_current_sys_admin, write_sys_audit

router = APIRouter()


# ─── Families ─────────────────────────────────────────────────────────────────

class FamilyCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "general"


@router.post("/families", summary="Create Prompt Family")
def create_family(
    body: FamilyCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    existing = db.query(PromptFamily).filter(PromptFamily.name == body.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Family '{body.name}' already exists")
    family = PromptFamily(name=body.name, description=body.description, category=body.category)
    db.add(family)
    db.commit()
    write_sys_audit(db, action="prompt_family_create", resource_type="prompt_family",
                    actor_sys_admin_id=admin.id, resource_id=str(family.id),
                    after_state={"name": family.name})
    return {"id": str(family.id), "name": family.name}


@router.get("/families", summary="List Prompt Families")
def list_families(db: Session = Depends(get_db), admin: SystemAdmin = Depends(get_current_sys_admin)):
    families = db.query(PromptFamily).filter(PromptFamily.is_active == True).all()
    return [
        {"id": str(f.id), "name": f.name, "description": f.description, "category": f.category}
        for f in families
    ]


from pydantic import BaseModel, ConfigDict

# ... (other imports)

# ─── Versions ─────────────────────────────────────────────────────────────────

class VersionCreateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_target: str = "gemini-1.5-pro"
    system_prompt: str
    user_prompt_template: str
    guardrails: dict[str, Any] = {}


@router.post("/families/{family_id}/versions", summary="Create Draft Prompt Version")
def create_version(
    family_id: UUID,
    body: VersionCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    family = db.query(PromptFamily).filter(PromptFamily.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Auto-increment version number
    last = (
        db.query(PromptVersion)
        .filter(PromptVersion.family_id == family_id)
        .order_by(PromptVersion.version.desc())
        .first()
    )
    next_version = (last.version + 1) if last else 1

    pv = PromptVersion(
        family_id=family_id,
        version=next_version,
        status="draft",
        model_target=body.model_target,
        system_prompt=body.system_prompt,
        user_prompt_template=body.user_prompt_template,
        guardrails=body.guardrails,
        created_by=admin.id,
    )
    db.add(pv)
    db.commit()
    write_sys_audit(db, action="prompt_version_create", resource_type="prompt_version",
                    actor_sys_admin_id=admin.id, resource_id=str(pv.id),
                    after_state={"family": family.name, "version": next_version, "status": "draft"})
    return {"id": str(pv.id), "family": family.name, "version": next_version, "status": "draft"}


@router.get("/families/{family_id}/versions", summary="List Versions for Family")
def list_versions(
    family_id: UUID,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    versions = (
        db.query(PromptVersion)
        .filter(PromptVersion.family_id == family_id)
        .order_by(PromptVersion.version.desc())
        .all()
    )
    return [
        {
            "id": str(v.id),
            "version": v.version,
            "status": v.status,
            "model_target": v.model_target,
            "guardrails": v.guardrails,
            "approved_at": v.approved_at.isoformat() if v.approved_at else None,
        }
        for v in versions
    ]


@router.post("/versions/{version_id}/approve", summary="Approve Prompt Version")
def approve_version(
    version_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    pv = db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    if not pv:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    if pv.status == "approved":
        raise HTTPException(status_code=400, detail="Already approved")

    before = {"status": pv.status}

    # Deprecate any previously approved version for this family
    db.query(PromptVersion).filter(
        PromptVersion.family_id == pv.family_id,
        PromptVersion.status == "approved",
        PromptVersion.id != pv.id,
    ).update({"status": "deprecated"})

    pv.status = "approved"
    pv.approved_by = admin.id
    pv.approved_at = datetime.utcnow()
    db.commit()

    write_sys_audit(db, action="prompt_version_approve", resource_type="prompt_version",
                    actor_sys_admin_id=admin.id, resource_id=str(version_id),
                    before_state=before, after_state={"status": "approved", "version": pv.version})
    return {"id": str(pv.id), "status": "approved", "version": pv.version}


@router.post("/versions/{version_id}/deprecate", summary="Deprecate Prompt Version")
def deprecate_version(
    version_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    pv = db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    if not pv:
        raise HTTPException(status_code=404, detail="Prompt version not found")

    before = {"status": pv.status}
    pv.status = "deprecated"
    db.commit()

    write_sys_audit(db, action="prompt_version_deprecate", resource_type="prompt_version",
                    actor_sys_admin_id=admin.id, resource_id=str(version_id),
                    before_state=before, after_state={"status": "deprecated"})
    return {"id": str(pv.id), "status": "deprecated"}


# ─── Prompt Runs ──────────────────────────────────────────────────────────────

@router.get("/runs", summary="List Prompt Runs")
def list_runs(
    tenant_id: Optional[UUID] = Query(None),
    family: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    q = db.query(PromptRun)
    if tenant_id:
        q = q.filter(PromptRun.tenant_id == tenant_id)
    if family:
        q = q.filter(PromptRun.family_name == family)
    if status:
        q = q.filter(PromptRun.status == status)
    total = q.count()
    runs = q.order_by(PromptRun.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(r.id),
                "tenant_id": str(r.tenant_id),
                "family_name": r.family_name,
                "version": r.version,
                "status": r.status,
                "guardrail_result": r.guardrail_result,
                "token_usage": r.token_usage,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
    }
