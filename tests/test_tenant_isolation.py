"""
Tenant Isolation Tests — Verify cross-tenant data cannot be accessed.
"""
import pytest
import uuid
from httpx import AsyncClient
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.billing import Wallet
from app.models.voice import CRMVoiceRecording
from app.security import create_access_token, get_password_hash


@pytest.fixture
def tenant_b(db, seed_plans):
    """Second tenant for isolation testing."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Tenant B",
        slug=f"tenant-b-{uuid.uuid4().hex[:4]}",
        is_active=True,
        plan_id=seed_plans["enterprise"].id,
    )
    db.add(tenant)
    db.flush()
    wallet = Wallet(id=uuid.uuid4(), tenant_id=tenant.id, balance=100.0)
    db.add(wallet)
    db.flush()
    return tenant


@pytest.fixture
def user_b(db, tenant_b):
    """User belonging to Tenant B."""
    user = User(
        id=uuid.uuid4(),
        email="userb@test.com",
        hashed_password=get_password_hash("test123"),
        full_name="User B",
        role=UserRole.ADMIN.value,
        tenant_id=tenant_b.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def token_b(user_b):
    return create_access_token(
        subject=user_b.email,
        additional_claims={"tenant_id": str(user_b.tenant_id), "role": user_b.role},
    )


@pytest.mark.asyncio
async def test_tenant_a_cannot_see_tenant_b_voice_recordings(
    client: AsyncClient, db, token_enterprise, user_b, tenant_b
):
    """User from Tenant A cannot access Tenant B's voice recording."""
    # Create a recording for Tenant B
    recording = CRMVoiceRecording(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        file_path="/uploads/test.wav",
        file_name="test.wav",
        file_hash="abc123hash",
    )
    db.add(recording)
    db.flush()

    # Try access from Tenant A
    headers = {"Authorization": f"Bearer {token_enterprise}"}
    resp = await client.get(
        f"/api/v1/crm/ai/voice/status/{recording.id}",
        headers=headers,
    )
    # Should fail — either 404 (not found for this tenant) or 403
    assert resp.status_code in [404, 403]


@pytest.mark.asyncio
async def test_followup_rules_tenant_isolated(
    client: AsyncClient, db, token_enterprise, token_b
):
    """Rules created by Tenant A are not visible to Tenant B."""
    # Create rule as Enterprise (Tenant A)
    headers_a = {"Authorization": f"Bearer {token_enterprise}"}
    resp = await client.post(
        "/api/v1/crm/followups/rules",
        json={
            "name": "Tenant A Rule",
            "template_body": "Hello {{first_name}}",
            "delay_minutes": 60,
        },
        headers=headers_a,
    )
    assert resp.status_code == 200

    # List rules as Tenant B
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp = await client.get("/api/v1/crm/followups/rules", headers=headers_b)
    assert resp.status_code == 200
    rules = resp.json()
    for rule in rules:
        assert rule["name"] != "Tenant A Rule"
