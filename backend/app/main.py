from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import (
    auth, billing, tenant, users,
    crm, campaigns, whatsapp,
    ai_voice, ai_vision, hunter, ai_brain, toolbox, sourcing, financial, execution, operations, scheduling,
    waha_webhook,
    leads, admin, stripe, trade, followups
)
settings = get_settings()

# Disable docs in production
_docs_url = None if getattr(settings, 'ENVIRONMENT', 'development') == 'production' else '/docs'
_redoc_url = None if getattr(settings, 'ENVIRONMENT', 'development') == 'production' else '/redoc'
_openapi_url = None if getattr(settings, 'ENVIRONMENT', 'development') == 'production' else f"{settings.API_V1_STR}/openapi.json"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Artin Smart Trade — AI Trade Operating System",
    version="2.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url
)

# --- API Routers ---
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(tenant.router, prefix=f"{settings.API_V1_STR}/tenants", tags=["tenants"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(hunter.router, prefix=f"{settings.API_V1_STR}/hunter", tags=["Hunter"])
app.include_router(ai_brain.router, prefix=f"{settings.API_V1_STR}/brain", tags=["Brain"])
app.include_router(toolbox.router, prefix=f"{settings.API_V1_STR}/toolbox", tags=["Toolbox"])
app.include_router(sourcing.router, prefix=f"{settings.API_V1_STR}/sourcing", tags=["sourcing"])
app.include_router(financial.router, prefix=f"{settings.API_V1_STR}/finance", tags=["finance"])
app.include_router(execution.router, prefix=f"{settings.API_V1_STR}/execution", tags=["execution"])
app.include_router(operations.router, prefix=f"{settings.API_V1_STR}/operations", tags=["operations"])
app.include_router(scheduling.router, prefix=f"{settings.API_V1_STR}/scheduling", tags=["scheduling"])
app.include_router(waha_webhook.router, prefix=f"{settings.API_V1_STR}/waha", tags=["waha-bot"])
app.include_router(whatsapp.router, prefix=f"{settings.API_V1_STR}/whatsapp", tags=["whatsapp"])
app.include_router(leads.router, prefix=f"{settings.API_V1_STR}/leads", tags=["leads"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(stripe.router, prefix=f"{settings.API_V1_STR}/stripe", tags=["stripe"])
app.include_router(trade.router, prefix=f"{settings.API_V1_STR}/trade", tags=["trade-intelligence"])
app.include_router(crm.router, prefix=f"{settings.API_V1_STR}/crm", tags=["crm"])
app.include_router(campaigns.router, prefix=f"{settings.API_V1_STR}/campaigns", tags=["campaigns"])
app.include_router(followups.router, prefix=f"{settings.API_V1_STR}/crm/followups", tags=["followups"])
app.include_router(ai_voice.router, prefix=f"{settings.API_V1_STR}/crm/ai/voice", tags=["voice-intelligence"])
app.include_router(ai_vision.router, prefix=f"{settings.API_V1_STR}/crm/ai/vision", tags=["vision-intelligence"])
app.include_router(billing.router, prefix=f"{settings.API_V1_STR}/billing", tags=["billing"])

# CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://trade.artinsmartagent.com",
    "https://admin.artinsmartagent.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0", "platform": "AI Trade OS"}

# Startup Events
from app.services.followup_service import start_followup_scheduler
from app.services.ai_worker import AIWorkerService
import asyncio

async def ai_watchdog_loop():
    """Periodically recover stuck AI jobs (every 5 minutes)."""
    while True:
        try:
            AIWorkerService.recover_stuck_jobs()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"AI watchdog error: {e}")
        await asyncio.sleep(300)  # 5 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_followup_scheduler())
    # Recover any stuck jobs from previous restart
    AIWorkerService.recover_stuck_jobs()
    # Start periodic watchdog
    asyncio.create_task(ai_watchdog_loop())
