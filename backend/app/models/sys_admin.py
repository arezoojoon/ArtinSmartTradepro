"""
Phase 6 System Admin Models
System administrators, audit logging, and RLS bypass infrastructure
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum, JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"

class DomainStatus(str, Enum):
    PENDING_DNS = "pending_dns"
    ACTIVE = "active"
    DISABLED = "disabled"

class PromptVersionStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"

class PromptRunStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    GUARDRAIL_REJECTED = "guardrail_rejected"

class EvalStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class SystemAdmin(Base):
    __tablename__ = "system_admins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    name = Column(String(255), nullable=True)
    role = Column(String(50), server_default='admin', nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    actor_sys_admin_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255), nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        {"schema": "public"},
    )

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    monthly_price_usd = Column(Integer, nullable=True)
    features = Column(JSON, nullable=True)
    limits = Column(JSON, nullable=True)
    is_active = Column(Boolean, server_default='true', nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    subscriptions = relationship("TenantSubscription", back_populates="plan")
    
    __table_args__ = (
        {"schema": "public"},
    )

class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    plan_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    plan = relationship("Plan", back_populates="subscriptions")
    
    __table_args__ = (
        {"schema": "public"},
    )

class UsageCounter(Base):
    __tablename__ = "usage_counters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    period_key = Column(String(7), nullable=False, index=True)  # YYYY-MM format
    metric = Column(String(50), nullable=False, index=True)
    value = Column(Integer, server_default='0', nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

class WhitelabelConfig(Base):
    __tablename__ = "whitelabel_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    is_enabled = Column(Boolean, server_default='false', nullable=False, index=True)
    brand_name = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color
    accent_color = Column(String(7), nullable=True)  # Hex color
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(50), nullable=True)
    custom_css = Column(Text, nullable=True)
    favicon_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    domains = relationship("WhitelabelDomain", back_populates="config")
    
    __table_args__ = (
        {"schema": "public"},
    )

class WhitelabelDomain(Base):
    __tablename__ = "whitelabel_domains"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(Enum(DomainStatus), nullable=False)
    verification_token = Column(String(255), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    dns_check_required = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    config = relationship("WhitelabelConfig", back_populates="domains")
    
    __table_args__ = (
        {"schema": "public"},
    )

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    is_default = Column(Boolean, server_default='false', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

class PromptFamily(Base):
    __tablename__ = "prompt_families"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    versions = relationship("PromptVersion", back_populates="family")
    
    __table_args__ = (
        {"schema": "public"},
    )

class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    status = Column(Enum(PromptVersionStatus), nullable=False, index=True)
    model_target = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    guardrails = Column(JSON, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    family = relationship("PromptFamily", back_populates="versions")
    runs = relationship("PromptRun", back_populates="prompt_version")
    evals = relationship("PromptEval", back_populates="prompt_version")
    
    __table_args__ = (
        {"schema": "public"},
    )

class PromptRun(Base):
    __tablename__ = "prompt_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    family_name = Column(String(255), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    engine_run_id = Column(UUID(as_uuid=True), nullable=True)
    input = Column(JSON, nullable=False)
    output = Column(JSON, nullable=False)
    token_usage = Column(JSON, nullable=True)
    guardrail_result = Column(JSON, nullable=True)
    status = Column(Enum(PromptRunStatus), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    prompt_version = relationship("PromptVersion", back_populates="runs")
    
    __table_args__ = (
        {"schema": "public"},
    )

class PromptEval(Base):
    __tablename__ = "prompt_evals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    test_name = Column(String(255), nullable=False)
    input = Column(JSON, nullable=False)
    expected_rules = Column(JSON, nullable=False)
    status = Column(Enum(EvalStatus), nullable=False)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    prompt_version = relationship("PromptVersion", back_populates="evals")
    
    __table_args__ = (
        {"schema": "public"},
    )

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, server_default='false', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )
