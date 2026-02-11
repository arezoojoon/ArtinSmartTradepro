"""
Test Configuration & Fixtures — Artin Smart Trade.
Provides: test DB, test client, mock tenants (Professional/Enterprise),
mock Gemini, mock Stripe webhooks.
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

# Use SQLite for tests to avoid Postgres dependency
TEST_DATABASE_URL = "sqlite:///./test.db"

# ─── Patch DB before importing app ────────────────────────────────────
import app.config as config_mod

_original_get_settings = config_mod.get_settings


def _get_test_settings():
    s = _original_get_settings()
    s.DATABASE_URL = TEST_DATABASE_URL
    s.SECRET_KEY = "test-secret-key-for-testing-only"
    s.GEMINI_API_KEY_1 = "fake-key-1"
    s.GEMINI_API_KEY_2 = "fake-key-2"
    s.GEMINI_API_KEY_3 = "fake-key-3"
    s.STRIPE_WEBHOOK_SECRET = ""
    return s


config_mod.get_settings = _get_test_settings

from app.models.base import Base
from app.database import get_db
from app.main import app as fastapi_app
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.billing import Wallet, WalletTransaction
from app.models.subscription import Plan, PlanFeature, Subscription
from app.models.ai_job import AIJob, AIUsage
from app.security import create_access_token, get_password_hash
from app.constants import Feature, PlanName, DEFAULT_PLAN_FEATURES


# ─── Engine & Session ─────────────────────────────────────────────────
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Per-test DB session with transaction rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def override_get_db(db):
    """Override FastAPI get_db dependency."""
    def _override():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _override
    yield
    fastapi_app.dependency_overrides.clear()


# ─── Plan & Feature Fixtures ─────────────────────────────────────────

@pytest.fixture
def seed_plans(db: Session):
    """Create Professional and Enterprise plans with features."""
    plans = {}
    for plan_name in [PlanName.PROFESSIONAL, PlanName.ENTERPRISE, PlanName.WHITE_LABEL]:
        plan = Plan(
            id=uuid.uuid4(),
            name=plan_name,
            display_name=plan_name.capitalize(),
            price_monthly=0,
            is_active=True,
        )
        db.add(plan)
        db.flush()

        features = DEFAULT_PLAN_FEATURES.get(plan_name, [])
        for feature_key in features:
            pf = PlanFeature(id=uuid.uuid4(), plan_id=plan.id, feature_key=feature_key)
            db.add(pf)

        plans[plan_name] = plan

    db.flush()
    return plans


# ─── Tenant Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def tenant_professional(db: Session, seed_plans):
    """Professional-tier tenant with wallet."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Pro Corp",
        slug=f"pro-corp-{uuid.uuid4().hex[:4]}",
        is_active=True,
        plan_id=seed_plans[PlanName.PROFESSIONAL].id,
    )
    db.add(tenant)
    db.flush()

    wallet = Wallet(id=uuid.uuid4(), tenant_id=tenant.id, balance=100.0)
    db.add(wallet)
    db.flush()
    return tenant


@pytest.fixture
def tenant_enterprise(db: Session, seed_plans):
    """Enterprise-tier tenant with wallet."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Enterprise Inc",
        slug=f"ent-inc-{uuid.uuid4().hex[:4]}",
        is_active=True,
        plan_id=seed_plans[PlanName.ENTERPRISE].id,
    )
    db.add(tenant)
    db.flush()

    wallet = Wallet(id=uuid.uuid4(), tenant_id=tenant.id, balance=500.0)
    db.add(wallet)
    db.flush()
    return tenant


@pytest.fixture
def user_professional(db: Session, tenant_professional):
    """User on Professional plan."""
    user = User(
        id=uuid.uuid4(),
        email="pro@test.com",
        hashed_password=get_password_hash("test123"),
        full_name="Pro User",
        role=UserRole.ADMIN.value,
        tenant_id=tenant_professional.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def user_enterprise(db: Session, tenant_enterprise):
    """User on Enterprise plan."""
    user = User(
        id=uuid.uuid4(),
        email="ent@test.com",
        hashed_password=get_password_hash("test123"),
        full_name="Ent User",
        role=UserRole.ADMIN.value,
        tenant_id=tenant_enterprise.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def token_professional(user_professional):
    """JWT token for Professional user."""
    return create_access_token(
        subject=user_professional.email,
        additional_claims={
            "tenant_id": str(user_professional.tenant_id),
            "role": user_professional.role,
        },
    )


@pytest.fixture
def token_enterprise(user_enterprise):
    """JWT token for Enterprise user."""
    return create_access_token(
        subject=user_enterprise.email,
        additional_claims={
            "tenant_id": str(user_enterprise.tenant_id),
            "role": user_enterprise.role,
        },
    )


# ─── Async Client ────────────────────────────────────────────────────

@pytest.fixture
async def client(override_get_db):
    """Async test client."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── Gemini Mocks ────────────────────────────────────────────────────

@pytest.fixture
def mock_gemini_success():
    """Mock Gemini API returning valid JSON response."""
    mock_response = MagicMock()
    mock_response.text = '{"transcript": "Hello", "sentiment": "POSITIVE", "intent": "Purchase Inquiry", "action_items": ["Follow up"], "key_topics": ["pricing"], "urgency": "high", "confidence": 0.9, "disclaimer": "AI-generated."}'

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch("app.services.gemini_service._get_model", return_value=mock_model) as m:
        yield m


@pytest.fixture
def mock_gemini_failure():
    """Mock Gemini API raising an exception."""
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("Gemini API rate limited")

    with patch("app.services.gemini_service._get_model", return_value=mock_model) as m:
        yield m


@pytest.fixture
def mock_gemini_vision_success():
    """Mock Gemini API for business card scan."""
    mock_response = MagicMock()
    mock_response.text = '{"name": "John Doe", "company": "Acme Inc", "position": "CEO", "phone": "+971501234567", "email": "john@acme.com", "website": "acme.com", "linkedin": "", "address": "", "confidence": 0.95, "field_confidence": {"name": 0.99, "company": 0.95, "phone": 0.9, "email": 0.92}}'

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch("app.services.gemini_service._get_model", return_value=mock_model) as m:
        yield m


@pytest.fixture
def mock_genai_upload():
    """Mock genai.upload_file for audio uploads."""
    mock_file = MagicMock()
    with patch("app.services.gemini_service.genai.upload_file", return_value=mock_file) as m:
        yield m
