"""
Advanced Tenant Settings for Phase 6
Custom pipelines, scoring weights, alert rules, and custom configurations
"""
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime

from .base import Base


class CustomPipeline(Base):
    """Custom deal pipelines for tenant"""
    __tablename__ = "custom_pipelines"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Pipeline details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pipeline stages
    stages = Column(JSON, nullable=False)  # Array of stage objects
    
    # Configuration
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="custom_pipelines")
    creator = relationship("User", back_populates="created_pipelines")
    deals = relationship("Deal", back_populates="custom_pipeline")


class ScoringProfile(Base):
    """Custom lead scoring profiles"""
    __tablename__ = "scoring_profiles"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Profile details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Scoring weights (0-100 scale)
    weights = Column(JSON, nullable=False)  # {"market_demand": 30, "payment_risk": 25, "regional_fit": 20, "engagement": 15, "data_quality": 10}
    
    # Thresholds
    qualified_threshold = Column(Integer, default=70, nullable=False)
    hot_threshold = Column(Integer, default=85, nullable=False)
    
    # Configuration
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="scoring_profiles")
    creator = relationship("User", back_populates="created_scoring_profiles")


class AlertRule(Base):
    """Custom alert rules for tenant"""
    __tablename__ = "alert_rules"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Rule details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Trigger conditions
    trigger_type = Column(String(50), nullable=False)  # usage_limit, risk_level, deal_stage, etc.
    trigger_config = Column(JSON, nullable=False)  # Configuration for trigger
    
    # Alert configuration
    alert_channels = Column(JSON, nullable=False)  # Array of channels: email, webhook, slack
    alert_message_template = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="alert_rules")
    creator = relationship("User", back_populates="created_alert_rules")


class CustomEmailTemplate(Base):
    """Custom email templates for tenant"""
    __tablename__ = "custom_email_templates"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Template details
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # welcome, notification, marketing, etc.
    subject = Column(String(200), nullable=False)
    
    # Template content
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    
    # Template variables
    variables = Column(JSON, nullable=True)  # Array of variable names
    
    # Status
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="custom_email_templates")
    creator = relationship("User", back_populates="created_email_templates")


class IntegrationConfig(Base):
    """Third-party integration configurations"""
    __tablename__ = "integration_configs"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Integration details
    integration_type = Column(String(50), nullable=False)  # slack, teams, webhook, etc.
    name = Column(String(100), nullable=False)
    
    # Configuration
    config = Column(JSON, nullable=False)  # Integration-specific configuration
    
    # Status
    is_enabled = Column(Boolean, default=False, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(20), default="never", nullable=False)  # never, success, error
    
    # Error handling
    last_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="integration_configs")
    creator = relationship("User", back_populates="created_integration_configs")


class ApiKey(Base):
    """API keys for tenant integrations"""
    __tablename__ = "api_keys"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Key details
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)  # Hashed API key
    key_prefix = Column(String(20), nullable=False)  # Prefix for identification
    
    # Permissions
    permissions = Column(JSON, nullable=False)  # Array of allowed endpoints/permissions
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    creator = relationship("User", back_populates="created_api_keys")


class WebhookConfig(Base):
    """Webhook configurations for tenant"""
    __tablename__ = "webhook_configs"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Webhook details
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=False)  # HMAC secret
    
    # Event types
    event_types = Column(JSON, nullable=False)  # Array of event types to send
    
    # Configuration
    retry_policy = Column(JSON, nullable=True)  # Retry configuration
    headers = Column(JSON, nullable=True)  # Custom headers
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="webhook_configs")
    creator = relationship("User", back_populates="created_webhook_configs")


class TenantPreference(Base):
    """General tenant preferences"""
    __tablename__ = "tenant_preferences"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Preference category and key
    category = Column(String(50), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    
    # Value (can be string, number, boolean, or JSON)
    value = Column(JSON, nullable=False)
    
    # Metadata
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="preferences")
    updater = relationship("User", back_populates="updated_preferences")


class FeatureFlag(Base):
    """Feature flags for tenant"""
    __tablename__ = "feature_flags"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Flag details
    key = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Flag value
    is_enabled = Column(Boolean, nullable=False)
    
    # Targeting (optional)
    user_roles = Column(JSON, nullable=True)  # Array of roles this flag applies to
    user_ids = Column(JSON, nullable=True)  # Array of specific user IDs
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="feature_flags")
    creator = relationship("User", back_populates="created_feature_flags")
    updater = relationship("User", back_populates="updated_feature_flags")
