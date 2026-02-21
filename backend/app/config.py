from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Artin Smart Trade"
    API_V1_STR: str = "/api/v1"
    
    # Security — MUST be overridden via .env or environment
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "artin_trade"
    DATABASE_URL: str = ""
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # AI
    GEMINI_API_KEY_1: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""
    
    # WhatsApp
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "artin_webhook_verify_2026"
    
    # WAHA Bot
    WAHA_API_URL: str = "http://localhost:3000"
    WAHA_SESSION: str = "default"
    WAHA_API_KEY: str = ""
    WAHA_PHONE_NUMBER: str = ""  # Bot's WhatsApp number (e.g. 971XXXXXXX)
    WAHA_WEBHOOK_SECRET: str = ""
    DEFAULT_TENANT_ID: str = "00000000-0000-0000-0000-000000000001"
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Admin — MUST be overridden via .env or environment
    FIRST_SUPERUSER: str = "admin@artin.com"
    FIRST_SUPERUSER_PASSWORD: str = ""

    # Phase 6 — Super Admin (SYS)
    SYS_ADMIN_JWT_SECRET: str = ""       # Override in .env; falls back to dev value
    SYS_ADMIN_RATE_LIMIT_PER_MIN: int = 30
    SYS_ADMIN_IP_ALLOWLIST: str = ""     # Comma-separated IPs; empty = unrestricted
    IMPERSONATION_TOKEN_EXPIRE_MINUTES: int = 15
    
    # Frontend origin for Stripe return URLs
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow unknown env vars (e.g. GOOGLE_API_KEY)

@lru_cache()
def get_settings():
    s = Settings()
    
    # Build DATABASE_URL dynamically if not explicitly set
    if not s.DATABASE_URL:
        s.DATABASE_URL = f"postgresql://{s.POSTGRES_USER}:{s.POSTGRES_PASSWORD}@{s.POSTGRES_SERVER}:{s.POSTGRES_PORT}/{s.POSTGRES_DB}"
    
    # Block unsafe defaults in production
    if s.ENVIRONMENT == "production":
        if not s.SECRET_KEY or s.SECRET_KEY in ("", "YOUR_SECRET_KEY_HERE_CHANGE_IN_PROD", "change_this_secret_in_prod"):
            raise RuntimeError("FATAL: SECRET_KEY must be set to a secure random value in production")
        if not s.FIRST_SUPERUSER_PASSWORD or s.FIRST_SUPERUSER_PASSWORD in ("", "admin123"):
            raise RuntimeError("FATAL: FIRST_SUPERUSER_PASSWORD must be set to a secure value in production")
        if not s.STRIPE_WEBHOOK_SECRET:
            raise RuntimeError("FATAL: STRIPE_WEBHOOK_SECRET must be set in production")
    
    # Provide a dev-only default for SECRET_KEY
    if not s.SECRET_KEY:
        s.SECRET_KEY = "dev-only-secret-key-NOT-FOR-PRODUCTION"
    
    return s
