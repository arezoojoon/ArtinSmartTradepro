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
    async def get_trade_data(db: Session, hs_code: str = None, country: str = None, year: int = None, limit: int = 50):
        """
        Fetch Trade Data from UN Comtrade Integration (Mock).
        Adapts the client response to match the frontend TradeRecord interface.
        """
        from app.integrations.uncomtrade import UNComtradeClient
        
        client = UNComtradeClient()
        # If no filters, use defaults to show something
        target_hs = hs_code or "091091"
        target_country = country or "World" 
        
        # The client returns a list of years for one pair
        raw_data = await client.get_trade_data(target_hs, target_country)
        
        formatted_results = []
        for row in raw_data:
            # Create two records (Import and Export) to match frontend structure
            common = {
                "hs_code": row["hs_code"],
                "reporter_country": row["reporter"],
                "partner_country": row["partner"],
                "year": row["year"],
                "quantity_unit": "kg", # Mock
                "quantity": 0 # Client doesn't return qty yet, defaulting
            }
            
            # Export Record
            if row.get("export_value_usd", 0) > 0:
                formatted_results.append({
                    **common,
                    "trade_flow": "export",
                    "trade_value_usd": row["export_value_usd"]
                })
                
            # Import Record
            if row.get("import_value_usd", 0) > 0:
                formatted_results.append({
                    **common,
                    "trade_flow": "import",
                    "trade_value_usd": row["import_value_usd"]
                })
                
        # Filter by year if requested
        if year:
            formatted_results = [r for r in formatted_results if r["year"] == year]
            
        return formatted_results

    @staticmethod
    def get_latest_fx_sync(db, base, quote):
        # Synchronous wrapper if needed or fallback
        pass
    
    @staticmethod
    async def get_freight_rate(db: Session, origin: str, dest: str, equipment: str = "20GP"):
        """
        Fetch Freight Rate from Freight Integration (Mock).
        """
        from app.integrations.freight import FreightClient
        
        client = FreightClient()
        raw = await client.get_rates(origin, dest, equipment)
        
        # Map to frontend expected shape
        return {
            "origin_country": raw["origin"],
            "destination_country": raw["destination"],
            "equipment_type": raw["container"],
            "rate_amount": raw["price_usd"],
            "currency": "USD",
            "transit_days_estimate": raw["transit_time_days"],
            "provider": raw["provider"],
            "incoterm": "CIF" # Default for now
        }

    @staticmethod
    async def get_latest_fx(db: Session, base: str, quote: str):
        """
        Fetch FX Rate from FX Integration (Mock).
        """
        from app.integrations.fx import FXClient
        
        client = FXClient()
        raw = await client.get_rate(base, quote)
        
        return {
            "base_currency": raw["base"],
            "quote_currency": raw["quote"],
            "rate": raw["rate"],
            "timestamp": datetime.datetime.now(), # generic
            "provider": raw["source"]
        }

    @staticmethod
    def seed_all_data(db: Session, current_user=None):
        """Legacy seeder - keeping empty or minimal if needed, but we use live integrations now."""
        pass
