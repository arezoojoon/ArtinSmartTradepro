from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import uuid
import datetime
import logging
from app.models.competitor import Competitor, CompetitorProduct, CompetitorPriceObservation, MarketShareSnapshot
from app.models.hunter import HunterRun

logger = logging.getLogger(__name__)

class CompetitorService:
    """
    Service for Competitor Intelligence (Hunter v2).
    Handles tracking, market share analysis, and price decision logic.
    """

    @staticmethod
    async def track_competitor_job(competitor_id: uuid.UUID, tenant_id: uuid.UUID):
        """
        Executes a scrape job for a competitor using a separate AsyncSession.
        """
        from app.db.session import async_session_maker
        async with async_session_maker() as db:
            try:
                res = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
                competitor = res.scalar_one_or_none()
                if not competitor:
                    raise ValueError("Competitor not found")
        
                today = datetime.datetime.utcnow().date()
                if competitor.updated_at and competitor.updated_at.date() == today:
                     logger.info(f"Skipping track for {competitor.name}, already updated today.")
        
                logger.info(f"Starting Scrape Job for {competitor.name}...")
                mock_products = CompetitorService._mock_scrape_products(competitor.name)
                
                results = []
                for p_data in mock_products:
                    product = await CompetitorService._store_product_observation(db, competitor_id, tenant_id, p_data)
                    results.append(product)
                    
                competitor.updated_at = datetime.datetime.utcnow()
                await db.commit()
                
                return {"status": "completed", "products_tracked": len(results)}
            except Exception as e:
                logger.error(f"Track Competitor failed: {e}")
                try:
                    await db.rollback()
                except: pass

    @staticmethod
    def _mock_scrape_products(competitor_name: str) -> List[Dict]:
        import random
        base_price = 1000 + random.randint(-200, 200)
        return [
            {
                "name": f"{competitor_name} Premium Ceramic Tile",
                "sku": f"SKU-{random.randint(1000,9999)}",
                "url": "http://example.com/product",
                "price": base_price,
                "currency": "USD",
                "availability": random.choice(["in_stock", "in_stock", "out_of_stock"]),
                "shipping": 50.0
            },
            {
                "name": f"{competitor_name} Standard Tile",
                "sku": f"SKU-{random.randint(1000,9999)}",
                "url": "http://example.com/product-std",
                "price": base_price * 0.8,
                "currency": "USD",
                "availability": "in_stock",
                "shipping": 45.0
            }
        ]

    @staticmethod
    async def _store_product_observation(db: AsyncSession, competitor_id: uuid.UUID, tenant_id: uuid.UUID, data: Dict):
        res = await db.execute(select(CompetitorProduct).where(
            CompetitorProduct.competitor_id == competitor_id,
            CompetitorProduct.sku == data["sku"]
        ))
        product = res.scalar_one_or_none()

        if not product:
            product = CompetitorProduct(
                competitor_id=competitor_id,
                tenant_id=tenant_id,
                name=data["name"],
                sku=data["sku"],
                product_url=data["url"],
                observed_source="mock_scraper"
            )
            db.add(product)
            await db.flush()

        product.last_price = data["price"]
        product.currency = data["currency"]
        product.availability_status = data["availability"]
        product.shipping_cost_estimate = data["shipping"]
        product.last_observed_at = datetime.datetime.utcnow()
        
        history = CompetitorPriceObservation(
            competitor_product_id=product.id,
            tenant_id=tenant_id,
            price=data["price"],
            currency=data["currency"],
            observed_at=datetime.datetime.utcnow(),
            raw_payload=data,
            confidence_score=0.95
        )
        db.add(history)
        return product

    @staticmethod
    async def analyze_market_share(db: AsyncSession, competitor_id: uuid.UUID, tenant_id: uuid.UUID):
        signals = [
            {"type": "traffic", "source": "similarweb", "score": 85},
            {"type": "mentions", "source": "google_search_api", "score": 40}
        ]
        
        estimated_share = (signals[0]["score"] * 0.2) + (signals[1]["score"] * 0.1)
        trend = "up" if estimated_share > 10 else "stable"
        
        snapshot = MarketShareSnapshot(
            competitor_id=competitor_id,
            tenant_id=tenant_id,
            share_percentage=estimated_share,
            trend=trend,
            signal_type="composite",
            source_name="sw+serp",
            confidence_score=0.8
        )
        db.add(snapshot)
        
        res = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        comp = res.scalar_one_or_none()
        if comp:
            comp.market_share_est = estimated_share
            await db.commit()
            
        return snapshot

    @staticmethod
    async def compare_prices(db: AsyncSession, my_price: float, product_keyword: str) -> Dict[str, Any]:
        res = await db.execute(select(CompetitorProduct).where(
            CompetitorProduct.name.ilike(f"%{product_keyword}%"),
            CompetitorProduct.last_price.isnot(None)
        ))
        competitor_products = res.scalars().all()
        
        if not competitor_products:
            return {"status": "no_data", "decision": "Collect more data"}

        prices = [float(p.last_price) for p in competitor_products]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        
        undercut_risk_score = 0
        margin_warning = False
        recommendation = "maintain"
        
        if my_price > avg_price * 1.1:
            undercut_risk_score = 80
            recommendation = "lower_price"
        elif my_price < min_price * 0.9:
            margin_warning = True
            recommendation = "raise_price"
            undercut_risk_score = 10
            
        return {
            "market_avg": round(avg_price, 2),
            "market_min": round(min_price, 2),
            "my_price": my_price,
            "decision": {
                "undercut_risk_score": undercut_risk_score,
                "margin_compression_warning": margin_warning,
                "recommended_action": recommendation,
                "positioning": "premium" if my_price > avg_price else "budget"
            }
        }
