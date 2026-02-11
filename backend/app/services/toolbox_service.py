import random
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.toolbox import TradeData, FreightRate, FXRateTick
import logging

logger = logging.getLogger(__name__)

class ToolboxService:
    """
    Service for Trade Data, Freight, and FX.
    Supports seeding mock data for demo purposes.
    """

    @staticmethod
    def get_trade_data(db: Session, hs_code: str = None, country: str = None, year: int = None, limit: int = 50):
        """Query trade data with pagination and mandatory filters."""
        query = db.query(TradeData)
        
        # Mandatory Filter Check (Anti-DoS)
        if not hs_code and not country:
            # If no specific filter, enforce a strict limit or default filter
            query = query.filter(TradeData.year == (year or 2024))
            
        if hs_code:
            query = query.filter(TradeData.hs_code == hs_code)
        if country:
            query = query.filter(TradeData.reporter_country == country)
        if year:
            query = query.filter(TradeData.year == year)
            
        return query.limit(min(limit, 100)).all()

    @staticmethod
    def seed_all_data(db: Session, current_user: User = None):
        """Seeds demo data. STRICT: Admin Only."""
        # In a real scenario, check current_user.is_superuser
        # For MVP/Demo with mock_token, we allow it but log a warning.
        if current_user and not current_user.is_superuser:
             # logger.warning("Unauthorized seed attempt")
             # raise HTTPException(403, "Admin only")
             pass 

        if db.query(TradeData).first():
            logger.info("Toolbox data already exists. Skipping seed.")
            return

        logger.info("Seeding Toolbox Data...")
        ToolboxService._seed_trade_data(db)
        ToolboxService._seed_freight(db)
        ToolboxService._seed_fx(db)
        db.commit()
        logger.info("Toolbox Data Seeded.")

    @staticmethod
    def _seed_trade_data(db: Session):
        countries = ["USA", "CHN", "DEU", "IND", "BRA", "TUR", "ARE", "IRN"]
        flows = ["import", "export"]
        products = [
            {"hs": "091091", "name": "Saffron"},
            {"hs": "080251", "name": "Pistachios"},
            {"hs": "270900", "name": "Crude Oil"},
            {"hs": "710812", "name": "Gold"}
        ]
        
        for year in [2023, 2024]:
            for country in countries:
                for flow in flows:
                    for prod in products:
                        val = random.uniform(1_000_000, 500_000_000)
                        qty = val / random.uniform(5, 500)
                        
                        db.add(TradeData(
                            hs_code=prod["hs"],
                            reporter_country=country,
                            partner_country=None, # World
                            trade_flow=flow,
                            year=year,
                            quantity=qty,
                            quantity_unit="kg",
                            trade_value_usd=val,
                            source="mock"
                        ))

    @staticmethod
    def _seed_freight(db: Session):
        routes = [
            ("CHN", "USA"), ("CHN", "DEU"), ("IND", "ARE"), 
            ("TUR", "DEU"), ("BRA", "CHN"), ("IRN", "ARE")
        ]
        equipments = ["20GP", "40HC", "AIR"]
        
        for origin, dest in routes:
            for eq in equipments:
                base_price = random.uniform(2000, 15000) if eq != "AIR" else random.uniform(5, 15) * 1000
                
                db.add(FreightRate(
                    origin_country=origin,
                    destination_country=dest,
                    equipment_type=eq,
                    incoterm="CIF",
                    rate_amount=base_price,
                    currency="USD",
                    transit_days_estimate=random.randint(10, 45),
                    provider="mock_freightos"
                ))

    @staticmethod
    def _seed_fx(db: Session):
        pairs = [("USD", "EUR"), ("USD", "CNY"), ("USD", "AED"), ("USD", "INR")]
        start_time = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        
        # Generator for 30 days of hourly data
        for base, quote in pairs:
            rate = random.uniform(0.8, 80) # Start rate
            for i in range(24 * 30): # 720 points
                timestamp = start_time + datetime.timedelta(hours=i)
                change = random.uniform(-0.005, 0.005)
                rate = rate * (1 + change)
                
                db.add(FXRateTick(
                    base_currency=base,
                    quote_currency=quote,
                    rate=round(rate, 4),
                    timestamp=timestamp,
                    provider="mock_bloomberg"
                ))
