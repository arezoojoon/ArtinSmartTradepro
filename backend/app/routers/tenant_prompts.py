"""
Tenant read-only access to prompt families and active versions.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.phase6 import PromptFamily, PromptVersion

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/families", summary="List Prompt Families (read-only)")
def list_families(db: Session = Depends(get_db)):
    families = db.query(PromptFamily).filter(PromptFamily.is_active == True).all()
    return [
        {"id": str(f.id), "name": f.name, "description": f.description, "category": f.category}
        for f in families
    ]


@router.get("/families/{name}/active-version", summary="Get Active Prompt Version for Family")
def get_active_version(name: str, db: Session = Depends(get_db)):
    family = db.query(PromptFamily).filter(PromptFamily.name == name, PromptFamily.is_active == True).first()
    if not family:
        raise HTTPException(status_code=404, detail=f"Prompt family '{name}' not found")

    version = (
        db.query(PromptVersion)
        .filter(PromptVersion.family_id == family.id, PromptVersion.status == "approved")
        .order_by(PromptVersion.version.desc())
        .first()
    )
    if not version:
        raise HTTPException(
            status_code=503,
            detail=f"No approved version for family '{name}'. NOT IMPLEMENTED / awaiting approval.",
        )

    return {
        "family_name": family.name,
        "version": version.version,
        "model_target": version.model_target,
        "status": version.status,
        "guardrails": version.guardrails,
    }
