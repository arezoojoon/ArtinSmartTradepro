"""
Phase 6 — System Admin, Plans, White-label, Prompt Ops
All models use the project's shared Base from app.models.base
"""
import uuid
import enum as py_enum
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer,
    Text, JSON, ForeignKey, UniqueConstraint, Index, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa

from .base import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class SubscriptionStatus(str, py_enum.Enum):
    ACTIVE      = "active"
    PAST_DUE    = "past_due"
    CANCELED    = "canceled"


class DomainStatus(str, py_enum.Enum):
    PENDING_DNS = "pending_dns"
    ACTIVE      = "active"
    DISABLED    = "disabled"


class PromptVersionStatus(str, py_enum.Enum):
    DRAFT      = "draft"
    APPROVED   = "approved"
    DEPRECATED = "deprecated"


class PromptRunStatus(str, py_enum.Enum):
    SUCCESS            = "success"
    GUARDRAIL_REJECTED = "guardrail_rejected"
    ERROR              = "error"


# ─── System Admin ─────────────────────────────────────────────────────────────

class SystemAdmin(Base):
    __tablename__ = "system_admins"

    email          = Column(String(255), nullable=False, unique=True, index=True)
    password_hash  = Column(String(255), nullable=False)
    name           = Column(String(255), nullable=True)
    is_active      = Column(Boolean, server_default="true", nullable=False, index=True)
    last_login_at  = Column(DateTime(timezone=True), nullable=True)


# ─── Audit Log ────────────────────────────────────────────────────────────────

class SysAuditLog(Base):
    """Phase 6 extended audit log — supports sys admin actions with before/after."""
    __tablename__ = "sys_audit_logs"

    tenant_id          = Column(UUID(as_uuid=True), nullable=True, index=True)
    actor_user_id      = Column(UUID(as_uuid=True), nullable=True)
    actor_sys_admin_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    action             = Column(String(100), nullable=False, index=True)
    resource_type      = Column(String(50),  nullable=False)
    resource_id        = Column(String(255), nullable=True)
    before_state       = Column(JSON, nullable=True)
    after_state        = Column(JSON, nullable=True)
    extra              = Column("metadata", JSON, nullable=True)   # DB col: metadata
    ip_address         = Column(String(45),  nullable=True)
    user_agent         = Column(String(500), nullable=True)


# ─── Plans & Entitlements ─────────────────────────────────────────────────────

class SysPlan(Base):
    """
    Phase 6 Plan — JSONB features + limits, no Stripe coupling.
    Separate from the legacy subscription.Plan (which is Stripe-based).
    """
    __tablename__ = "sys_plans"

    code               = Column(String(50),  nullable=False, unique=True, index=True)
    name               = Column(String(255), nullable=False)
    description        = Column(Text,  nullable=True)
    monthly_price_usd  = Column(Numeric(10, 2), nullable=True)   # informational only
    features           = Column(JSON,  nullable=False, server_default="{}")
    # limits example: {"messages_sent_daily": 500, "leads_created_monthly": 200,
    #                   "brain_runs_daily": 50, "seats": 5, "whitelabel": false}
    limits             = Column(JSON,  nullable=False, server_default="{}")
    is_active          = Column(Boolean, server_default="true", nullable=False, index=True)

    subscriptions = relationship("TenantSubscription", back_populates="plan")


class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"

    tenant_id            = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    plan_id              = Column(UUID(as_uuid=True), ForeignKey("sys_plans.id"), nullable=False)
    status               = Column(
        sa.Enum("active", "past_due", "canceled", name="sub_status_enum"),
        nullable=False,
        server_default="active"
    )
    current_period_start = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    current_period_end   = Column(DateTime(timezone=True), nullable=True)

    plan = relationship("SysPlan", back_populates="subscriptions")


class UsageCounter(Base):
    __tablename__ = "usage_counters"

    tenant_id  = Column(UUID(as_uuid=True), nullable=False, index=True)
    period_key = Column(String(10), nullable=False, index=True)  # "2026-02" or "2026-02-21"
    metric     = Column(String(50), nullable=False, index=True)
    value      = Column(Integer, server_default="0", nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "period_key", "metric", name="uq_usage_counters"),
    )


# ─── White-label ──────────────────────────────────────────────────────────────

class WhitelabelConfig(Base):
    __tablename__ = "whitelabel_configs"

    tenant_id     = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    is_enabled    = Column(Boolean, server_default="false", nullable=False)
    brand_name    = Column(String(255), nullable=True)
    logo_url      = Column(String(500), nullable=True)
    favicon_url   = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)   # hex, e.g. "#3A7BD5"
    accent_color  = Column(String(7), nullable=True)
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(50), nullable=True)
    custom_css    = Column(Text, nullable=True)

    domains = relationship("WhitelabelDomain", back_populates="config")


class WhitelabelDomain(Base):
    __tablename__ = "whitelabel_domains"

    tenant_id          = Column(UUID(as_uuid=True), nullable=False, index=True)
    domain             = Column(String(255), nullable=False, unique=True, index=True)
    status             = Column(
        sa.Enum("pending_dns", "active", "disabled", name="domain_status_enum"),
        nullable=False,
        server_default="pending_dns"
    )
    verification_token = Column(String(255), nullable=True)
    verified_at        = Column(DateTime(timezone=True), nullable=True)
    config_id          = Column(UUID(as_uuid=True), ForeignKey("whitelabel_configs.id"), nullable=True)

    config = relationship("WhitelabelConfig", back_populates="domains")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    tenant_id  = Column(UUID(as_uuid=True), nullable=False, index=True)
    name       = Column(String(255), nullable=False)
    type       = Column(String(50), nullable=False, index=True)
    subject    = Column(String(500), nullable=False)
    body       = Column(Text, nullable=False)
    is_default = Column(Boolean, server_default="false", nullable=False)


# ─── Prompt Ops ───────────────────────────────────────────────────────────────

class PromptFamily(Base):
    __tablename__ = "prompt_families"

    name        = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category    = Column(String(50), nullable=False, server_default="general")
    is_active   = Column(Boolean, server_default="true", nullable=False)

    versions = relationship("PromptVersion", back_populates="family")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    family_id            = Column(UUID(as_uuid=True), ForeignKey("prompt_families.id"), nullable=False, index=True)
    version              = Column(Integer, nullable=False)
    status               = Column(
        sa.Enum("draft", "approved", "deprecated", name="prompt_status_enum"),
        nullable=False,
        server_default="draft",
        index=True
    )
    model_target         = Column(String(100), nullable=False, server_default="gemini-1.5-pro")
    system_prompt        = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    # guardrails example:
    # {"no_numeric_without_data": true, "must_cite_profiles": true,
    #  "require_insufficient_data_notice": false}
    guardrails           = Column(JSON, nullable=False, server_default="{}")
    created_by           = Column(UUID(as_uuid=True), nullable=False)   # sys_admin_id or user_id
    approved_by          = Column(UUID(as_uuid=True), nullable=True)
    approved_at          = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("family_id", "version", name="uq_prompt_family_version"),
    )

    family = relationship("PromptFamily", back_populates="versions")
    runs   = relationship("PromptRun", back_populates="prompt_version")
    evals  = relationship("PromptEval", back_populates="prompt_version")


class PromptRun(Base):
    __tablename__ = "prompt_runs"

    tenant_id       = Column(UUID(as_uuid=True), nullable=False, index=True)
    family_name     = Column(String(255), nullable=False, index=True)
    version         = Column(Integer, nullable=False)
    prompt_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=True, index=True)
    engine_run_id   = Column(UUID(as_uuid=True), nullable=True)
    input           = Column(JSON, nullable=False)
    output          = Column(JSON, nullable=True)
    token_usage     = Column(JSON, nullable=True)
    guardrail_result = Column(JSON, nullable=True)   # {"pass": bool, "reasons": []}
    status          = Column(
        sa.Enum("success", "guardrail_rejected", "error", name="prompt_run_status_enum"),
        nullable=False,
        server_default="success",
        index=True
    )
    error_message   = Column(Text, nullable=True)

    prompt_version = relationship("PromptVersion", back_populates="runs")


class PromptEval(Base):
    __tablename__ = "prompt_evals"

    family_id      = Column(UUID(as_uuid=True), ForeignKey("prompt_families.id"), nullable=False, index=True)
    version        = Column(Integer, nullable=False)
    prompt_version_id = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=True)
    test_name      = Column(String(255), nullable=False)
    input          = Column(JSON, nullable=False)
    # expected_rules example:
    # {"must_contain": ["INSUFFICIENT DATA"], "must_not_contain_numbers": true,
    #  "must_have_profile_ids": false}
    expected_rules = Column(JSON, nullable=False)
    last_status    = Column(String(20), nullable=True)   # "passed" | "failed" | null
    last_result    = Column(JSON, nullable=True)
    last_run_at    = Column(DateTime(timezone=True), nullable=True)

    prompt_version = relationship("PromptVersion", back_populates="evals")


# ─── System Settings ──────────────────────────────────────────────────────────

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key          = Column(String(100), nullable=False, unique=True, index=True)
    value        = Column(JSON, nullable=False)
    description  = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, server_default="false", nullable=False)
