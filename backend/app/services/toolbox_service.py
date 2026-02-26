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
        rate_amount = raw["price_usd"]

        # Generate route-aware port risks based on origin/destination
        port_risks = [
            {
                "port": f"Origin ({origin})",
                "level": "Moderate" if raw["transit_time_days"] > 25 else "Low",
                "issue": "Port congestion may add 2-3 day delays" if raw["transit_time_days"] > 25 else "Normal operations"
            },
            {
                "port": f"Destination ({dest})",
                "level": "Low",
                "issue": "Normal operations"
            },
        ]
        if raw["transit_time_days"] > 30:
            port_risks.append({
                "port": "Transit (Long Route)",
                "level": "High",
                "issue": "Extended transit — vessel rerouting or weather delays expected"
            })

        # Estimate hidden costs proportional to rate
        thc = round(rate_amount * 0.08)
        customs = round(rate_amount * 0.05)
        baf = round(rate_amount * 0.10)
        hidden_costs = [
            {"item": "Terminal Handling Charges (THC)", "est": thc, "type": "Origin"},
            {"item": "Customs Clearance Fees", "est": customs, "type": "Destination"},
            {"item": "Bunker Adjustment Factor (BAF)", "est": baf, "type": "Freight"},
        ]
        if raw.get("trend") == "increasing":
            hidden_costs.append({"item": "Peak Season Surcharge (PSS)", "est": round(rate_amount * 0.12), "type": "Freight"})

        return {
            "origin_country": raw["origin"],
            "destination_country": raw["destination"],
            "equipment_type": raw["container"],
            "rate_amount": rate_amount,
            "currency": "USD",
            "transit_days_estimate": raw["transit_time_days"],
            "provider": raw["provider"],
            "incoterm": "CIF",
            "port_risks": port_risks,
            "hidden_costs": hidden_costs,
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
    async def get_fx_history(base: str, quote: str, days: int = 30):
        """
        Generate server-side historical FX data using deterministic seeding.
        Uses the currency pair as seed so the same pair always produces consistent data.
        """
        import hashlib

        # Seed based on pair for deterministic results within the same day
        today = datetime.datetime.utcnow().date()
        seed_str = f"{base}{quote}{today.isoformat()}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Base rates (same as FXClient)
        rates_map = {
            "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "AED": 3.67,
            "CNY": 7.15, "INR": 83.5, "JPY": 149.5, "SAR": 3.75,
        }
        base_val = rates_map.get(base, 1.0)
        quote_val = rates_map.get(quote, 1.0)
        current_rate = quote_val / base_val

        data = []
        rate = current_rate * rng.uniform(0.97, 1.0)
        for i in range(days, -1, -1):
            d = today - datetime.timedelta(days=i)
            change = (rng.random() - 0.5) * (rate * 0.012)
            rate += change
            data.append({
                "date": d.strftime("%b %d"),
                "rate": round(rate, 4),
                "upper": round(rate * 1.02, 4),
                "lower": round(rate * 0.98, 4),
            })

        return data

    @staticmethod
    def seed_all_data(db: Session, current_user=None):
        """Legacy seeder - keeping empty or minimal if needed, but we use live integrations now."""
        pass
