"""
Plan Gating Tests — Verify @require_feature blocks unauthorized access.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_professional_blocked_from_trade_intelligence(
    client: AsyncClient, token_professional
):
    """Professional plan cannot access Enterprise-only trade endpoints."""
    headers = {"Authorization": f"Bearer {token_professional}"}
    resp = await client.post(
        "/api/v1/trade/analyze/seasonal",
        json={"product": "cocoa", "region": "europe"},
        headers=headers,
    )
    assert resp.status_code == 403
    assert "plan upgrade" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enterprise_can_access_trade_intelligence(
    client: AsyncClient, token_enterprise, mock_gemini_success
):
    """Enterprise plan CAN access trade endpoints."""
    headers = {"Authorization": f"Bearer {token_enterprise}"}
    resp = await client.post(
        "/api/v1/trade/analyze/seasonal",
        json={"product": "cocoa", "region": "europe"},
        headers=headers,
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_professional_blocked_from_voice(
    client: AsyncClient, token_professional
):
    """Professional plan cannot access Voice Intelligence."""
    headers = {"Authorization": f"Bearer {token_professional}"}
    resp = await client.post(
        "/api/v1/crm/ai/voice/analyze",
        headers=headers,
        files={"file": ("test.wav", b"fake audio data", "audio/wav")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_professional_blocked_from_vision(
    client: AsyncClient, token_professional
):
    """Professional plan cannot access Vision Intelligence."""
    headers = {"Authorization": f"Bearer {token_professional}"}
    resp = await client.post(
        "/api/v1/crm/ai/vision/scan",
        headers=headers,
        files={"file": ("card.jpg", b"fake image data", "image/jpeg")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_professional_blocked_from_brain(
    client: AsyncClient, token_professional
):
    """Professional plan cannot access Brain Intelligence."""
    headers = {"Authorization": f"Bearer {token_professional}"}
    resp = await client.post(
        "/api/v1/brain/decide",
        json={
            "product": "cocoa",
            "origin_country": "Ghana",
            "destination_country": "Germany",
            "quantity_kg": 1000,
            "budget_usd": 50000,
        },
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_no_auth_returns_401(client: AsyncClient):
    """No auth token should return 401 on all protected endpoints."""
    endpoints = [
        ("POST", "/api/v1/trade/analyze/seasonal"),
        ("POST", "/api/v1/crm/ai/voice/analyze"),
        ("POST", "/api/v1/crm/ai/vision/scan"),
        ("POST", "/api/v1/brain/decide"),
        ("GET", "/api/v1/admin/tenants"),
        ("POST", "/api/v1/whatsapp/send"),
    ]
    for method, url in endpoints:
        if method == "POST":
            resp = await client.post(url)
        else:
            resp = await client.get(url)
        assert resp.status_code == 401, f"{method} {url} returned {resp.status_code}"
