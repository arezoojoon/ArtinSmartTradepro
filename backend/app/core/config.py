import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra='ignore', env_file=".env", case_sensitive=True)
    # App
    APP_NAME: str = "Artin Smart Trade"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/artin_trade"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://trade.artinsmartagent.com"
    ]
    
    # Email
    EMAIL_PROVIDER: str = "local_dev"  # local_dev, smtp, sendgrid
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # Billing
    BILLING_PROVIDER: str = "local_stub"  # stripe, local_stub
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    
    # Plans
    PROFESSIONAL_PLAN_PRICE: int = 29900  # $299.00 in cents
    ENTERPRISE_PLAN_PRICE: int = 99900   # $999.00 in cents
    WHITELABEL_PLAN_PRICE: int = 299900  # $2,999.00 in cents
    WHITELABEL_SETUP_FEE: int = 50000    # $500.00 setup fee
    
    # Rate Limiting
    LOGIN_RATE_LIMIT: int = 5  # attempts per minute
    FORGOT_PASSWORD_RATE_LIMIT: int = 3  # attempts per hour


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
