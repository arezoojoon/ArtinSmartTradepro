from .base import Base
from .user import User
from .tenant import Tenant, TenantMembership, TenantInvitation
from .auth import Session, PasswordResetToken, EmailVerificationToken
from .billing import Wallet, WalletTransaction, BillingCustomer, Invoice
from .subscription import Subscription, Plan, PlanFeature
from .audit import AuditLog
from .whatsapp import WhatsAppMessage
from .crm import (
    CRMCompany, CRMContact, CRMPipeline, CRMDeal, 
    CRMNote, CRMTag, CRMConversation, CRMInvoice, CRMTask
)
from .campaign import CRMCampaign, CRMCampaignSegment, CRMCampaignMessage
from .followup import CRMFollowUpRule, CRMFollowUpExecution, CRMRevenueAttribution
from .hunter import HunterRun, HunterResult, TradeSignal
from .ai_job import AIJob, AIUsage
from .bot_session import BotDeeplinkRef, BotSession, BotEvent, WAHAWebhookEvent, WhatsAppStatusUpdate
# Deal models
from .deal import (
    Deal, DealStatus, DealPriority, DealPriceComponent, 
    DealDocument, DealMilestone, DealRiskAssessment, 
    DealCommunication, DealTemplate
)
# Brain models
from .brain import (
    ArbitrageResult, RiskAssessment, DemandForecast, 
    CulturalStrategy, TradeOpportunity, MarketSignal, BrainEngineRun
)
# Phase 6 models
from .phase6 import (
    SystemAdmin,
    SysAuditLog,
    SysPlan,
    TenantSubscription,
    UsageCounter,
    WhitelabelConfig,
    WhitelabelDomain,
    EmailTemplate,
    PromptFamily,
    PromptVersion,
    PromptRun,
    PromptEval,
    SystemSetting,
)

# Tenant settings models
from .tenant_settings import (
    CustomPipeline,
    ScoringProfile,
    AlertRule,
    CustomEmailTemplate,
    IntegrationConfig,
    ApiKey,
    WebhookConfig,
    TenantPreference,
    FeatureFlag,
)

# Revenue models
from .billing_revenue import (
    RevenueSnapshot,
    RevenueEvent,
    ChurnPrediction,
    RevenueAlert,
)

# Billing Extended & Provisioning
from .billing_ext import (
    BillingCheckoutSession,
    StripeEvent,
    ProvisioningStatus,
    CheckoutSessionStatus,
    ProvisioningState
)

# Cost models
from .cost_tracking import (
    CostMetric,
    CostBudget,
    CostAlert,
    CostForecast,
    CostOptimization,
    CostSummary,
)

# Support models
from .support_ticket import (
    SupportTicket,
    TicketMessage,
    TicketAttachment,
    TicketTimeLog,
    TicketTemplate,
    TicketSla,
    TicketMetrics,
)

# Email Outbox
from .email import EmailOutbox

# Logistics models
from .logistics import (
    Shipment, ShipmentPackage, ShipmentEvent, Carrier,
    ShipmentStatus, ShipmentEventType,
)

# Acquisition Expo models
from .representative import Representative
from .catalog import Catalog

