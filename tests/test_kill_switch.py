"""
Kill Switch Tests — Verify tenant disable blocks all access.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_kill_switch_blocks_api_access(
    client: AsyncClient, db, token_enterprise, tenant_enterprise
):
    """When tenant is disabled, all API calls return 403."""
    headers = {"Authorization": f"Bearer {token_enterprise}"}

    # Verify access works before
    resp = await client.get("/api/v1/leads/stats", headers=headers)
    assert resp.status_code == 200

    # KILL SWITCH: disable tenant
    tenant_enterprise.is_active = False
    db.flush()

    # All endpoints should now return 403
    resp = await client.get("/api/v1/leads/stats", headers=headers)
    assert resp.status_code == 403
    assert "suspended" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_kill_switch_blocks_login(
    client: AsyncClient, db, user_enterprise, tenant_enterprise
):
    """When tenant is disabled, login is blocked."""
    tenant_enterprise.is_active = False
    db.flush()

    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "ent@test.com", "password": "test123"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_kill_switch_reactivation(
    client: AsyncClient, db, token_enterprise, tenant_enterprise
):
    """After re-enabling tenant, access is restored."""
    headers = {"Authorization": f"Bearer {token_enterprise}"}

    # Disable
    tenant_enterprise.is_active = False
    db.flush()
    resp = await client.get("/api/v1/leads/stats", headers=headers)
    assert resp.status_code == 403

    # Re-enable
    tenant_enterprise.is_active = True
    db.flush()
    resp = await client.get("/api/v1/leads/stats", headers=headers)
    assert resp.status_code == 200
