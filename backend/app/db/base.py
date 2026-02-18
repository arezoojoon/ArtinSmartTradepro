from app.models.base import Base

# Import all models here so SQLAlchemy mappers can resolve all relationships.
# This file serves as a central registry for all models.
from app.models.email import EmailOutbox
from app.models.user import User
from app.models.tenant import Tenant, TenantMembership, TenantInvitation
from app.models.crm import CRMCompany, CRMContact, CRMConversation, CRMDeal
from app.models.whatsapp import WhatsAppMessage
from app.models.subscription import Subscription, Plan, PlanFeature
from app.models.billing import Wallet, WalletTransaction, BillingCustomer, Invoice
from app.models.campaign import CRMCampaign, CRMCampaignSegment, CRMCampaignMessage
from app.models.followup import CRMFollowUpRule, CRMFollowUpExecution, CRMRevenueAttribution
from app.models.hunter import HunterRun, HunterResult, TradeSignal
from app.models.bot_session import BotSession, BotEvent, BotDeeplinkRef
from app.models.audit import AuditLog
from app.models.ai_job import AIJob
from app.models.lead import Lead
from app.models.scheduling import AvailabilitySlot, Appointment

