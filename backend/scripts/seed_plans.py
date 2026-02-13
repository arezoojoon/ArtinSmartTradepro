import logging
from app.database import SessionLocal, engine
from app.models.base import Base

# Import ALL models to ensure they are registered with Base.metadata
# This is crucial for create_all() to work correctly
from app.models import (
    user, tenant, billing, subscription, crm, campaign, followup, lead, source,
    whatsapp, audit, voice, vision, ai_job, hunter, brain, execution, toolbox,
    bot_session, scheduling, product
)

from app.models.subscription import Plan, PlanFeature
from app.constants import PlanName, DEFAULT_PLAN_FEATURES
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed():
    # 1. Create Tables if they don't exist
    try:
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        # Proceeding might fail, but let's try
    
    # 2. Seed Plans
    db = SessionLocal()
    try:
        # Check DB connection first
        db.execute(text("SELECT 1"))
        logger.info("Database connected.")
        
        plans = [
            {"name": PlanName.PROFESSIONAL, "display_name": "Professional", "price_monthly": 29.99, "price_yearly": 299.99},
            {"name": PlanName.ENTERPRISE, "display_name": "Enterprise", "price_monthly": 99.99, "price_yearly": 999.99},
            {"name": PlanName.WHITE_LABEL, "display_name": "White Label", "price_monthly": 299.99, "price_yearly": 2999.99},
        ]

        for p_data in plans:
            existing = db.query(Plan).filter(Plan.name == p_data["name"]).first()
            if not existing:
                logger.info(f"Creating plan: {p_data['name']}")
                plan = Plan(**p_data)
                db.add(plan)
            else:
                logger.info(f"Plan exists: {p_data['name']}")
                # Ensure we have the plan object
                plan = existing

            # Seed Features
            features = DEFAULT_PLAN_FEATURES.get(p_data["name"], [])
            for feature_key in features:
                existing_feat = db.query(PlanFeature).filter(
                    PlanFeature.plan_id == plan.id,
                    PlanFeature.feature_key == feature_key
                ).first()
                if not existing_feat:
                    logger.info(f"  + Adding feature: {feature_key}")
                    pf = PlanFeature(plan_id=plan.id, feature_key=feature_key, limit_value=None)
                    db.add(pf)
        
        db.commit()
        logger.info("Plans seeded successfully!")
    except Exception as e:
        logger.error(f"Error seeding plans: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
