from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import logging

from .core.config import settings
from .api.routes import auth, tenants
from .db.session import engine
from .db.base import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable docs in production
docs_url = None if settings.ENVIRONMENT == "production" else "/docs"
redoc_url = None if settings.ENVIRONMENT == "production" else "/redoc"
openapi_url = None if settings.ENVIRONMENT == "production" else "/openapi.json"

app = FastAPI(
    title=settings.APP_NAME,
    description="Artin Smart Trade — AI Trade Operating System",
    version=settings.APP_VERSION,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])

# Import CRM router dynamically or at top level if prefered, but keeping style:
from .api.routes import crm
app.include_router(crm.router, prefix="/api/v1/crm", tags=["crm"])

from .routers import hunter
app.include_router(hunter.router, prefix="/api/v1/hunter", tags=["hunter"])

# Step 4D: WAHA Bot + CRM Follow-Ups
from .routers import followups, whatsapp, waha_webhook
app.include_router(followups.router, prefix="/api/v1/followups", tags=["followups"])
app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["whatsapp"])
app.include_router(waha_webhook.router, prefix="/api/v1/waha", tags=["waha"])

# --- Health Check ---
@app.get("/health")
def health_check():
    return {
        "status": "ok", 
        "version": settings.APP_VERSION, 
        "platform": "AI Trade OS",
        "environment": settings.ENVIRONMENT
    }

# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"exception": str(exc), "type": type(exc).__name__}
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {}
            }
        }
    )

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and services."""
    logger.info("Starting up Artin Smart Trade API...")
    
    try:
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created/verified")
        logger.info("Artin Smart Trade API started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't fail startup - let the app start and handle DB errors per request
        logger.warning("API starting without database verification")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Artin Smart Trade API...")
