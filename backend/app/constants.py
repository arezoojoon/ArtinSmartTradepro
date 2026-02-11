"""
Canonical Feature Constants — Single Source of Truth.
Every @require_feature() call MUST use these constants.
NO magic strings anywhere.
"""

class Feature:
    # --- Phase 1 (Professional) ---
    LEAD_HUNTER = "lead_hunter"
    CSV_IMPORT = "csv_import"
    CRM_BASIC = "crm_basic"
    WHATSAPP_SINGLE = "whatsapp_single"
    
    # --- Phase 2 (Enterprise) ---
    CRM_ADVANCED = "crm_advanced"
    WHATSAPP_BROADCAST = "whatsapp_broadcast"
    FOLLOW_UP = "follow_up"
    TRADE_INTELLIGENCE = "trade_intelligence"
    BRAND_DATA = "brand_data"
    SHIPPING_TOOLS = "shipping_tools"
    AI_VISION = "ai_vision"
    AI_VOICE = "ai_voice"
    AI_BRAIN = "ai_brain"
    CAMPAIGNS = "campaigns"
    REPORTS = "reports"
    GAP_ANALYSIS = "gap_analysis"
    
    # --- Phase 3 (White Label) ---
    CUSTOM_DOMAIN = "custom_domain"
    CUSTOM_API = "custom_api"
    DEDICATED_SERVER = "dedicated_server"


class PlanName:
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    WHITE_LABEL = "white_label"


# Default seed data — used ONLY for initial DB population.
# After seed, all lookups come from DB.
DEFAULT_PLAN_FEATURES = {
    PlanName.PROFESSIONAL: [
        Feature.LEAD_HUNTER,
        Feature.CSV_IMPORT,
        Feature.CRM_BASIC,
        Feature.WHATSAPP_SINGLE,
    ],
    PlanName.ENTERPRISE: [
        Feature.LEAD_HUNTER,
        Feature.CSV_IMPORT,
        Feature.CRM_BASIC,
        Feature.CRM_ADVANCED,
        Feature.WHATSAPP_SINGLE,
        Feature.WHATSAPP_BROADCAST,
        Feature.FOLLOW_UP,
        Feature.TRADE_INTELLIGENCE,
        Feature.BRAND_DATA,
        Feature.SHIPPING_TOOLS,
        Feature.AI_VISION,
        Feature.AI_VOICE,
        Feature.AI_BRAIN,
        Feature.CAMPAIGNS,
        Feature.REPORTS,
        Feature.GAP_ANALYSIS,
    ],
    PlanName.WHITE_LABEL: ["*"],  # Wildcard — all features
}
