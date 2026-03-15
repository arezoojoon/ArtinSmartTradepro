"""
Super Admin Reset Script
Run inside Docker:  docker compose exec backend python scripts/reset_superadmin.py
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models.user import User
from app.core.security import get_password_hash

settings = get_settings()

# --- CONFIG ---
SUPERADMIN_EMAIL = "superadmin@artin.com"
SUPERADMIN_PASSWORD = "Admin@Artin2026!"  # Change this after first login!
# ---------------

def reset_superadmin():
    db_url = settings.DATABASE_URL
    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        # Check if user exists
        user = session.execute(
            select(User).where(User.email == SUPERADMIN_EMAIL)
        ).scalar_one_or_none()
        
        if user:
            # Reset password and ensure superuser flags
            user.hashed_password = get_password_hash(SUPERADMIN_PASSWORD)
            user.is_superuser = True
            user.is_active = True
            user.email_verified = True
            user.role = "super_admin"
            session.commit()
            print(f"✅ Super Admin password RESET for: {SUPERADMIN_EMAIL}")
        else:
            # Also check admin@artin.com (the other default)
            alt_user = session.execute(
                select(User).where(User.email == "admin@artin.com")
            ).scalar_one_or_none()
            
            if alt_user:
                alt_user.hashed_password = get_password_hash(SUPERADMIN_PASSWORD)
                alt_user.is_superuser = True
                alt_user.is_active = True
                alt_user.email_verified = True
                alt_user.role = "super_admin"
                session.commit()
                print(f"✅ Super Admin password RESET for: admin@artin.com")
            else:
                # Create new superadmin
                new_user = User(
                    email=SUPERADMIN_EMAIL,
                    hashed_password=get_password_hash(SUPERADMIN_PASSWORD),
                    full_name="Super Admin",
                    is_active=True,
                    is_superuser=True,
                    email_verified=True,
                    role="super_admin",
                )
                session.add(new_user)
                session.commit()
                print(f"✅ Super Admin CREATED: {SUPERADMIN_EMAIL}")
        
        print(f"📧 Email: {SUPERADMIN_EMAIL}")
        print(f"🔑 Password: {SUPERADMIN_PASSWORD}")
        print(f"⚠️  Change this password immediately after login!")

if __name__ == "__main__":
    reset_superadmin()
