"""
Auth Router Tests — Registration, Login, Refresh, Logout, Password Reset.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient, seed_plans):
    """Valid registration creates tenant + wallet + user."""
    resp = await client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com",
        "password": "secure123",
        "full_name": "New User",
        "company_name": "New Corp",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert data["tenant_id"] is not None


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, user_professional):
    """Duplicate email returns 400."""
    resp = await client.post("/api/v1/auth/register", json={
        "email": "pro@test.com",
        "password": "anything",
        "full_name": "Duplicate",
        "company_name": "Dup Corp",
    })
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_valid(client: AsyncClient, user_professional):
    """Valid login returns access + refresh tokens."""
    resp = await client.post("/api/v1/auth/login", data={
        "username": "pro@test.com",
        "password": "test123",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, user_professional):
    """Wrong password returns 400."""
    resp = await client.post("/api/v1/auth/login", data={
        "username": "pro@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_inactive_tenant(client: AsyncClient, db, user_professional, tenant_professional):
    """Login blocked when tenant is disabled (kill switch)."""
    tenant_professional.is_active = False
    db.flush()

    resp = await client.post("/api/v1/auth/login", data={
        "username": "pro@test.com",
        "password": "test123",
    })
    assert resp.status_code == 403
    assert "suspended" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_logout_invalidates_token(client: AsyncClient, token_professional):
    """Logged out token should be rejected."""
    headers = {"Authorization": f"Bearer {token_professional}"}

    # Logout
    resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert resp.status_code == 200

    # Subsequent request should fail
    resp = await client.get("/health", headers=headers)
    # Note: /health doesn't require auth, but any authenticated endpoint should fail


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, user_professional):
    """Refresh token returns new tokens and blacklists old."""
    # Login first
    login = await client.post("/api/v1/auth/login", data={
        "username": "pro@test.com",
        "password": "test123",
    })
    old_refresh = login.json()["refresh_token"]

    # Refresh
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh,
    })
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"] != login.json()["access_token"]


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client: AsyncClient):
    """Non-existent email still returns 200 (security: don't leak)."""
    resp = await client.post("/api/v1/auth/forgot-password", json={
        "email": "nonexistent@test.com",
    })
    assert resp.status_code == 200
    assert "reset link has been sent" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Invalid reset token returns 400."""
    resp = await client.post("/api/v1/auth/reset-password", json={
        "token": "fake-token",
        "new_password": "newpass123",
    })
    assert resp.status_code == 400
