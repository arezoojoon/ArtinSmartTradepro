from app.models.base import Base

# Import all models here so Alembic or other tools can discover them
# This file serves as a central registry for all models
from app.models.email import EmailOutbox
from app.models.user import User
from app.models.tenant import Tenant, TenantMembership, TenantInvitation
from app.models.crm import CRMCompany
