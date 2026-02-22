"""
Trade Data Service - Real-time UN Comtrade Integration
Phase 6 Enhancement - Live trade data with HS Code lookup and analysis
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import aiohttp
import pandas as pd

from app.models.phase5 import AssetSeasonalityMatrix
from app.models.tenant import Tenant
from app.config import get_settings


class TradeDataService:
    """Service for accessing and analyzing trade data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key = get_settings().COMTRADE_API_KEY
        self.base_url = "https://comtrade.un.org"
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
    
    async def get_trade_data(
        self,
        reporter_code: str,
        partner_code: str,
        year: int,
        month: Optional[int] = None,
        product_code: Optional[str] = None,
        trade_flow: Optional[str] = None,
        aggregate_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get trade data from UN Comtrade API
        
        Args:
            reporter_code: Reporter code (e.g., 'all')
            partner_code: Partner code (e.g., 'all')
            year: Year (e.g., 2023)
            month: Month (1-12, optional)
            product_code: HS Code (optional)
            trade_flow: Trade flow (e.g., 'all', 'import', 'export')
            aggregate_by: Aggregation level (e.g., 'year', 'month', 'day')
        """
        # Build API URL
        url = f"{self.base_url}/api/v1/data"
        params = {
            "freq": aggregate_by or "M",
            "px": "HS",
            "r": "all",
            "ps": reporter_code,
            "p": partner_code,
            "yr": year,
            "rg": "all",
            "cc": "all"
        }
        
        if month:
            params["m"] = month
        if product_code:
            params["cc"] = product_code
        if trade_flow and trade_flow != "all":
            params["rg"] = trade_flow
        
        # Add API key
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_trade_data(data)
                    else:
                        raise Exception(f"API Error: {response.status} - {await response.text()}")
        except Exception as e:
            raise Exception(f"Trade data fetch failed: {str(e)}")
    
    def _process_trade_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw trade data from Comtrade API"""
        if "data" not in data:
            return {"error": "No data found"}
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data["data"])
        
        # Data validation and cleaning
        if df.empty:
            return {"error": "Empty dataset"}
        
        # Convert numeric columns
        numeric_columns = ["Trade Value", "Net Weight (kg)", "Gross Weight (kg)", "Trade Quantity", "Customs Value"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert date columns
        date_columns = ["Period", "Date"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return {
            "data": data["data"],
            "processed_count": len(df),
            "date_range": {
                "start": df["Date"].min().isoformat() if "Date" in df.columns else None,
                "end": df["Date"].max().isoformat() if "Date" in df.columns else None
            },
            "summary": self._generate_summary(df)
        }
    
    def _generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics from trade data"""
        if df.empty:
            return {}
        
        return {
            "total_records": len(df),
            "total_trade_value": float(df["Trade Value"].sum()) if "Trade Value" in df.columns else 0,
            "unique_reporters": df["Reporter"].nunique() if "Reporter" in df.columns else 0,
            "unique_partners": df["Partner"].nunique() if "Partner" in df.columns else 0,
            "unique_products": df["HS Code"].nunique() if "HS Code" in df.columns else 0,
            "top_products": df["HS Code"].value_counts().head(10).to_dict(),
            "top_countries": df["Partner"].value_counts().head(10).to_dict()
        }
    
    async def get_hs_code_info(self, hs_code: str) -> Dict[str, Any]:
        """Get detailed HS Code information"""
        # This would integrate with a database of HS codes
        # For now, return mock data
        hs_info_db = {
            "01011000": {
                "description": "Live bovine animals",
                "category": "Animals, live",
                "parent_code": "01",
                "chapter": "1",
                "heading": "Live bovine animals"
            },
            "01012100": {
                "description": "Meat of bovine animals, fresh or chilled",
                "category": "Meat of bovine animals, fresh or chilled",
                "parent_code": "01",
                "chapter": "1",
                "heading": "Meat of bovine animals, fresh or chilled"
            },
            "01021000": {
                "description": "Meat and edible meat offal",
                "category": "Meat and edible meat offal",
                "parent_code": "02",
                "chapter": "2",
                "import": "Meat and edible meat offal"
            },
            # Add more HS codes as needed
        }
        
        return hs_info_db.get(hs_code, {
            "description": f"HS Code {hs_code}",
            "category": "Unknown",
            "parent_code": None,
            "chapter": "Unknown",
            "heading": "Unknown"
        })
    
    async def analyze_trends(
        self,
        reporter_code: str,
        partner_code: str,
        product_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """Analyze trade trends over multiple years"""
        all_data = []
        
        for year in range(datetime.utcnow().year - years + 1, datetime.utcnow().year + 1):
            try:
                year_data = await self.get_trade_data(
                    reporter_code=reporter_code,
                    partner_code=partner_code,
                    year=year,
                    product_code=product_code
                )
                if "data" in year_data:
                    for record in year_data["data"]:
                        record["year"] = year
                    all_data.extend(year_data["data"])
            except Exception as e:
                print(f"Error fetching data for year {year}: {e}")
                continue
        
        if not all_data:
            return {"error": "No data available for analysis"}
        
        df = pd.DataFrame(all_data)
        
        # Convert date and numeric columns
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df["Trade Value"] = pd.to_numeric(df["Trade Value"], errors='coerce')
        
        # Group by year for trend analysis
        yearly_data = df.groupby(df["Date"].dt.year).agg({
            'total_value': ('Trade Value', 'sum'),
            'trade_count': ('Trade Value', 'count'),
            'avg_value': ('Trade Value', 'mean')
        }).reset_index()
        
        # Calculate growth rates
        yearly_data['growth_rate'] = yearly_data['total_value'].pct_change()
        
        return {
            "trend_data": yearly_data.to_dict('records'),
            "summary": {
                "years_analyzed": len(yearly_data),
                "total_value": float(yearly_data['total_value'].sum()),
                "avg_annual_growth": yearly_data['growth_rate'].mean(),
                "best_year": yearly_data.loc[yearly_data['total_value'].idxmax(), 'year'].values()[0] if not yearly_data.empty else None,
                "worst_year": yearly_data.loc[year_data['total_value'].idxmin(), 'year'].values()[0] if not yearly_data.empty else None
            }
        }
    
    async def get_export_opportunity_score(
        self,
        origin_country: str,
        destination_country: str,
        product_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate export opportunity score for country/product combination"""
        try:
            # Get recent trade data for the route
            recent_data = await self.get_trade_data(
                reporter_code=origin_country,
                partner_code=destination_country,
                year=datetime.utcnow().year,
                trade_flow="export"
            )
            
            if "data" not in recent_data:
                return {"error": "No trade data available"}
            
            df = pd.DataFrame(recent_data["data"])
            
            # Filter by product category if specified
            if product_category:
                df = df[df["HS Code"].str.startswith(product_category[:2])]
            
            if df.empty:
                return {"error": "No matching trade data found"}
            
            # Calculate opportunity score based on:
            # 1. Trade volume (40%)
            # 2. Growth rate (30%)
            # 3. Market concentration (20%)
            # 4. Data availability (10%)
            
            volume_score = min(len(df) / 1000, 1.0) * 40
            growth_score = 0.3  # Mock growth rate calculation
            concentration_score = 0.2  # Mock concentration score
            data_score = min(len(df) / 100, 1.0) * 10
            
            total_score = volume_score + growth_score + concentration_score + data_score
            
            return {
                "opportunity_score": total_score,
                "score_breakdown": {
                    "volume_score": volume_score,
                    "growth_score": growth_score,
                    "concentration_score": concentration_score,
                    "data_score": data_score
                },
                "data_points": len(df),
                "period": "last 12 months",
                "recommendation": self._get_recommendation(total_score)
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on opportunity score"""
        if score >= 0.8:
            return "High opportunity - Strong export potential"
        elif score >= 0.6:
            return "Moderate opportunity - Consider exploring"
        elif score >= 0.4:
            return "Low opportunity - Limited data"
        else:
            return "Very low opportunity - Insufficient data"
    
    async def get_competitor_analysis(
        self,
        product_code: str,
        origin_country: str,
        destination_country: str
    ) -> Dict[str, Any]:
        """Analyze competitor countries for a product/route"""
        try:
            # Get export data for origin country
            origin_exports = await self.get_trade_data(
                reporter_code=origin_country,
                partner_code="all",
                year=datetime.utcnow().year,
                product_code=product_code,
                trade_flow="export"
            )
            
            # Get import data for destination country
            dest_imports = await self.get_trade_data(
                reporter_code="all",
                partner_code=destination_country,
                year=datetime.utcnow().year,
                product_code=product_code,
                trade_flow="import"
            )
            
            # Get total exports and imports
            origin_df = pd.DataFrame(origin_exports.get("data", []))
            dest_df = pd.DataFrame(dest_imports.get("data", []))
            
            origin_total = origin_df["Trade Value"].sum() if not origin_df.empty else 0
            dest_total = dest_df["Trade Value"].sum() if not dest_df.empty else 0
            
            # Get top competitor countries
            top_exporters = origin_df.groupby("Partner")["Trade Value"].sum().sort_values(ascending=False)
            top_importers = dest_df.groupby("Reporter")["Trade Value"].sum().sort_values(ascending=False)
            
            return {
                "route": f"{origin_country} -> {destination_country}",
                "product_code": product_code,
                "origin_total_value": float(origin_total),
                "destination_total_value": float(dest_total),
                "trade_balance": float(origin_total - dest_total),
                "top_exporters": top_exporters.head(5).to_dict(),
                "top_importers": top_importers.head(5).to_dict(),
                "competitor_strength": "high" if origin_total > dest_total * 2 else "medium" if origin_total > dest_total else "low"
            }
            
        except Exception as e:
            return {"error": f"Competitor analysis failed: {str(e)}"}


# Helper function to get trade data service
def get_trade_data_service(db: Session) -> TradeDataService:
    """Get trade data service instance"""
    return TradeDataService(db)
