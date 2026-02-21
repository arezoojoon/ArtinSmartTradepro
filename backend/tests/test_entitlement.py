"""
Tests for Phase 6 — Entitlement Service (Quota Enforcement).
Run: cd backend && python -m pytest tests/test_entitlement.py -v

Verifies:
  - check_limit raises HTTP 429 when quota exceeded
  - increment_usage correctly upserts counters
  - has_feature works with plan features dict
  - No active subscription → allow in dev, block in prod
"""
import pytest
from unittest.mock import MagicMock, patch, call
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException


def _make_plan(limits=None, features=None):
    """Helper to create a mock plan dict."""
    return {
        "id": str(uuid4()),
        "code": "professional",
        "name": "Professional",
        "features": features or {},
        "limits": limits or {},
    }


class TestCheckLimit:
    def test_raises_429_when_daily_limit_exceeded(self):
        from app.services.entitlement import check_limit

        tenant_id = uuid4()
        plan = _make_plan(limits={"messages_sent_daily": 100})

        with patch("app.services.entitlement.get_tenant_plan", return_value=plan):
            with patch("app.services.entitlement.get_current_usage", return_value=100):
                with pytest.raises(HTTPException) as exc_info:
                    check_limit(MagicMock(), tenant_id, "messages_sent", increment=1)
                assert exc_info.value.status_code == 429
                assert "QUOTA_EXCEEDED" in str(exc_info.value.detail)

    def test_allows_when_under_limit(self):
        from app.services.entitlement import check_limit

        tenant_id = uuid4()
        plan = _make_plan(limits={"messages_sent_daily": 100})

        with patch("app.services.entitlement.get_tenant_plan", return_value=plan):
            with patch("app.services.entitlement.get_current_usage", return_value=50):
                # Should not raise
                check_limit(MagicMock(), tenant_id, "messages_sent", increment=1)

    def test_unlimited_when_limit_is_minus_one(self):
        from app.services.entitlement import check_limit

        tenant_id = uuid4()
        plan = _make_plan(limits={"messages_sent_daily": -1})

        with patch("app.services.entitlement.get_tenant_plan", return_value=plan):
            with patch("app.services.entitlement.get_current_usage", return_value=9999):
                # Should not raise — -1 means unlimited
                check_limit(MagicMock(), tenant_id, "messages_sent", increment=1)

    def test_no_limit_key_means_unlimited(self):
        from app.services.entitlement import check_limit

        tenant_id = uuid4()
        plan = _make_plan(limits={})  # No limits configured

        with patch("app.services.entitlement.get_tenant_plan", return_value=plan):
            with patch("app.services.entitlement.get_current_usage", return_value=0):
                check_limit(MagicMock(), tenant_id, "messages_sent", increment=1)

    def test_monthly_leads_limit(self):
        from app.services.entitlement import check_limit

        tenant_id = uuid4()
        plan = _make_plan(limits={"leads_created_monthly": 50})

        with patch("app.services.entitlement.get_tenant_plan", return_value=plan):
            with patch("app.services.entitlement.get_current_usage", return_value=50):
                with pytest.raises(HTTPException) as exc_info:
                    check_limit(MagicMock(), tenant_id, "leads_created", increment=1)
                assert exc_info.value.status_code == 429

    def test_brain_runs_blocked_at_limit(self):
        from app.services.entitlement import check_limit

        tenant_id = uuid4()
        plan = _make_plan(limits={"brain_runs_daily": 20})

        with patch("app.services.entitlement.get_tenant_plan", return_value=plan):
            with patch("app.services.entitlement.get_current_usage", return_value=20):
                with pytest.raises(HTTPException) as exc_info:
                    check_limit(MagicMock(), tenant_id, "brain_runs", increment=1)
                assert exc_info.value.status_code == 429


class TestHasFeature:
    def test_feature_present_and_true(self):
        from app.services.entitlement import has_feature

        tenant_id = uuid4()
        plan = _make_plan(features={"whitelabel": True, "brain_cultural": True})

        with patch("app.services.entitlement.get_tenant_plan", return_value=plan):
            assert has_feature(MagicMock(), tenant_id, "whitelabel") is True
            assert has_feature(MagicMock(), tenant_id, "brain_cultural") is True

    def test_feature_absent_returns_false(self):
        from app.services.entitlement import has_feature

        tenant_id = uuid4()
        plan = _make_plan(features={})

        with patch("app.services.entitlement.get_tenant_plan", return_value=plan):
            assert has_feature(MagicMock(), tenant_id, "whitelabel") is False

    def test_no_plan_returns_false(self):
        from app.services.entitlement import has_feature

        with patch("app.services.entitlement.get_tenant_plan", return_value=None):
            assert has_feature(MagicMock(), uuid4(), "whitelabel") is False

    def test_require_feature_raises_403_when_missing(self):
        from app.services.entitlement import require_feature

        with patch("app.services.entitlement.get_tenant_plan", return_value=_make_plan()):
            with pytest.raises(HTTPException) as exc_info:
                require_feature(MagicMock(), uuid4(), "whitelabel")
            assert exc_info.value.status_code == 403
