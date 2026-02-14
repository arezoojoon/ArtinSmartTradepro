import sys
import os

# Add parent dir to path so we can import 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
import uuid
from app.database import SessionLocal
import app.models # Force load all models (including Product) to resolve relationships
from app.models.user import User, UserRole, UserPersona
from app.models.tenant import Tenant, TenantMode
from app.models.billing import Wallet
from app.models.subscription import Plan
from app.security import get_password_hash
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_admin(email: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            logger.info(f"User {email} found.")
            user.hashed_password = get_password_hash(password)
            
            # Ensure proper role
            if user.role != UserRole.SUPER_ADMIN:
                logger.info(f"Promoting {email} to SUPER_ADMIN.")
                user.role = UserRole.SUPER_ADMIN
            
            db.commit()
            logger.info(f"Password for {email} updated successfully.")
        else:
            logger.info(f"User {email} not found. Creating new Super Admin...")
            
            # 1. Get a Plan (Default to first found or Professional)
            plan = db.query(Plan).first()
            if not plan:
                logger.error("No plans found in database. Run 'python scripts/seed_plans.py' first.")
                return

            # 2. Create Tenant
            tenant = Tenant(
                name="System Admin",
                slug="system-admin-" + str(uuid.uuid4())[:8],
                is_active=True,
                plan_id=plan.id,
                mode=TenantMode.HYBRID
            )
            db.add(tenant)
            db.flush()
            
            # 3. Create Wallet
            wallet = Wallet(tenant_id=tenant.id, balance=1000.0) # Give some credits
            db.add(wallet)
            
            # 4. Create User
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name="Super Admin",
                role=UserRole.SUPER_ADMIN,
                tenant_id=tenant.id,
                persona=UserPersona.BUSINESS_OWNER,
                is_active=True
            )
            db.add(user)
            db.commit()
            logger.info(f"Super Admin {email} created successfully.")
            
    except Exception as e:
        logger.error(f"Error resetting admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    settings = get_settings()
    email = settings.FIRST_SUPERUSER or "admin@artin.com"
    
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = "admin" # Default fallbadk
        print("No password provided. setting to 'admin'")
        
    print(f"--- Resetting Admin Password ---")
    print(f"User: {email}")
    print(f"New Password: {password}")
    
    reset_admin(email, password)
