from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"

class UserPersona(str, enum.Enum):
    TRADER = "trader"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    ADMIN = "admin"

class User(Base):
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String, default=UserRole.USER.value, nullable=False)
    
    # V3: User Persona for customized UX
    persona = Column(String, default=UserPersona.TRADER.value, nullable=False)
    
    # Multi-Tenancy (Many-to-Many via Membership)
    memberships = relationship("TenantMembership", back_populates="user")
    
    # Sessions
    sessions = relationship("Session", back_populates="user")

    # State
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    
    # Current tenant selection
    current_tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)

    # Deal relationships
    assigned_deals = relationship("Deal", foreign_keys="[Deal.assigned_to]", back_populates="assigned_user")
    created_deals = relationship("Deal", foreign_keys="[Deal.created_by]", back_populates="creator")
    uploaded_documents = relationship("DealDocument", foreign_keys="[DealDocument.uploaded_by]", back_populates="uploader")
    signed_documents = relationship("DealDocument", foreign_keys="[DealDocument.signed_by]", back_populates="signer")
    assigned_milestones = relationship("DealMilestone", back_populates="assignee")
    assessed_risks = relationship("DealRiskAssessment", back_populates="assessor")
    created_communications = relationship("DealCommunication", back_populates="creator")
    created_deal_templates = relationship("DealTemplate", back_populates="creator")
    
    # Advanced settings relationships
    created_pipelines = relationship("CustomPipeline", back_populates="creator")
    created_scoring_profiles = relationship("ScoringProfile", back_populates="creator")
    created_alert_rules = relationship("AlertRule", back_populates="creator")
    created_email_templates = relationship("CustomEmailTemplate", back_populates="creator")
    created_integration_configs = relationship("IntegrationConfig", back_populates="creator")
    created_api_keys = relationship("ApiKey", back_populates="creator")
    created_webhook_configs = relationship("WebhookConfig", back_populates="creator")
    updated_preferences = relationship("TenantPreference", back_populates="updater")
    created_feature_flags = relationship("FeatureFlag", back_populates="creator")
    updated_feature_flags = relationship("FeatureFlag", back_populates="updater")

    @property
    def tenant_id(self):
        """Alias for current_tenant_id used by plan_gate and routers."""
        return self.current_tenant_id
