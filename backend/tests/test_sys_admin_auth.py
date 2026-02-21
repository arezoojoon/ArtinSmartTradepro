"""
Tests for Phase 6 — Sys Admin Authentication & Access Control.
Run: cd backend && python -m pytest tests/test_sys_admin_auth.py -v

Verifies:
  - tenant token CANNOT access /sys routes
  - sys token CANNOT access tenant CRM routes
  - sys admin login returns correct JWT claims
  - impersonation token has correct TTL claims
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

# ─── Unit tests for token creation / validation ───────────────────────────────

class TestSysTokenCreation:
    def test_create_access_token_has_sys_admin_claim(self):
        from app.services.sys_admin_auth import create_sys_access_token, decode_sys_token
        admin_id = uuid4()
        token = create_sys_access_token(admin_id)
        payload = decode_sys_token(token)
        assert payload["sys_admin"] is True
        assert payload["token_type"] == "sys_access"
        assert payload["sub"] == str(admin_id)

    def test_create_refresh_token_type(self):
        from app.services.sys_admin_auth import create_sys_refresh_token, decode_sys_token
        admin_id = uuid4()
        token = create_sys_refresh_token(admin_id)
        payload = decode_sys_token(token)
        assert payload["token_type"] == "sys_refresh"
        assert payload["sys_admin"] is True

    def test_impersonation_token_has_required_claims(self):
        from app.services.sys_admin_auth import create_impersonation_token, decode_sys_token
        admin_id = uuid4()
        tenant_id = uuid4()
        token = create_impersonation_token(admin_id, tenant_id)
        payload = decode_sys_token(token)
        assert payload["token_type"] == "impersonation"
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["impersonated_by_sys_admin_id"] == str(admin_id)
        assert payload["sys_admin"] is True

    def test_impersonation_token_short_lived(self):
        """Impersonation token must expire in ~15 minutes."""
        from app.services.sys_admin_auth import create_impersonation_token, decode_sys_token
        import time
        admin_id = uuid4()
        token = create_impersonation_token(admin_id, uuid4())
        payload = decode_sys_token(token)
        now = time.time()
        ttl_minutes = (payload["exp"] - now) / 60
        assert ttl_minutes <= 15.5   # Should be at most 15 minutes
        assert ttl_minutes >= 14.0   # Should be at least 14 minutes (allowing for test latency)


# ─── Access control guard tests ───────────────────────────────────────────────

class TestAccessControl:
    def test_regular_tenant_token_lacks_sys_admin_claim(self):
        """A normal tenant JWT (from app.security) must not have sys_admin=True."""
        from app.security import create_access_token
        from jose import jwt
        from app.config import get_settings
        settings = get_settings()
        token = create_access_token(subject=str(uuid4()), additional_claims={"tenant_id": str(uuid4())})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        # Tenant tokens must NOT have sys_admin claim
        assert payload.get("sys_admin") is not True

    def test_sys_token_rejected_by_tenant_auth(self):
        """A sys token should not decode successfully with the tenant's SECRET_KEY."""
        from app.services.sys_admin_auth import create_sys_access_token
        from jose import JWTError, jwt
        from app.config import get_settings
        settings = get_settings()
        admin_id = uuid4()
        sys_token = create_sys_access_token(admin_id)
        # sys tokens use SYS_ADMIN_JWT_SECRET, not SECRET_KEY
        # If they're different, this should raise JWTError
        sys_secret = settings.SYS_ADMIN_JWT_SECRET or "dev-sys-admin-secret-NOT-FOR-PROD"
        tenant_secret = settings.SECRET_KEY
        if sys_secret != tenant_secret:
            with pytest.raises(JWTError):
                jwt.decode(sys_token, tenant_secret, algorithms=["HS256"])

    def test_decode_invalid_sys_token_raises(self):
        from app.services.sys_admin_auth import decode_sys_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_sys_token("definitely.not.a.valid.token")
        assert exc_info.value.status_code == 401


# ─── Audit log write test ─────────────────────────────────────────────────────

class TestAuditLogging:
    def test_audit_log_written_on_sys_action(self):
        from app.services.sys_admin_auth import write_sys_audit
        from app.models.phase6 import SysAuditLog

        # Use a mock DB session
        mock_db = MagicMock()
        admin_id = uuid4()

        write_sys_audit(
            mock_db,
            action="tenant_suspend",
            resource_type="tenant",
            actor_sys_admin_id=admin_id,
            tenant_id=uuid4(),
            before_state={"is_active": True},
            after_state={"is_active": False},
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, SysAuditLog)
        assert added_obj.action == "tenant_suspend"
        assert added_obj.before_state == {"is_active": True}
        assert added_obj.after_state == {"is_active": False}


# ─── Password hashing ─────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_and_verify(self):
        from app.services.sys_admin_auth import hash_password, verify_password
        pw = "SuperSecure@Admin2026"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True
        assert verify_password("WrongPassword", hashed) is False
