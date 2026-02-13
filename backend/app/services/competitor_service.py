from sqlalchemy.orm import Session
from sqlalchemy import func
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

    # --- Async Job Orchestration ---
    
    @staticmethod
    def track_competitor_job(competitor_id: uuid.UUID, tenant_id: uuid.UUID):
        """
        Enqueues a scrape job for a competitor.
        In a real system, this would push to Redis/Celery.
        For MVP, we execute synchronously but structure it as a job.
        
        Idempotency: Checks if we already scraped this competitor today.
        """
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
            if not competitor:
                raise ValueError("Competitor not found")
    
            # 1. Idempotency Check
            today = datetime.datetime.utcnow().date()
            # Mock idempotency check: assume if updated_at is today, we skip (unless forced)
            # Real impl would check a 'JobLog' table with (competitor_id + date) key.
            if competitor.updated_at and competitor.updated_at.date() == today:
                 logger.info(f"Skipping track for {competitor.name}, already updated today.")
                 # return {"status": "skipped", "reason": "idempotent"} 
                 # For demo, we allow re-run
    
            logger.info(f"Starting Scrape Job for {competitor.name}...")
            
            # 2. Mock Scrape Execution (Worker Logic)
            # In reality: fetch URL -> parse HTML -> extract products
            mock_products = CompetitorService._mock_scrape_products(competitor.name)
            
            # 3. Store Results & Update History
            results = []
            for p_data in mock_products:
                product = CompetitorService._store_product_observation(db, competitor_id, tenant_id, p_data)
                results.append(product)
                
            # 4. Update Competitor Timestamp
            competitor.updated_at = datetime.datetime.utcnow()
            db.commit()
            
            return {"status": "completed", "products_tracked": len(results)}
        finally:
            db.close()

    @staticmethod
    def _mock_scrape_products(competitor_name: str) -> List[Dict]:
        """Simulates scraper output."""
        # Returns randomized data for demo
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
    def _store_product_observation(db: Session, competitor_id: uuid.UUID, tenant_id: uuid.UUID, data: Dict):
        """
        Normalize and store observation. 
        Updates CompetitorProduct AND creates CompetitorPriceObservation.
        """
        # Find or Create Product
        product = db.query(CompetitorProduct).filter(
            CompetitorProduct.competitor_id == competitor_id,
            CompetitorProduct.sku == data["sku"]
        ).first()

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
            db.flush() # get ID

        # Update Current State
        product.last_price = data["price"]
        product.currency = data["currency"]
        product.availability_status = data["availability"]
        product.shipping_cost_estimate = data["shipping"]
        product.last_observed_at = datetime.datetime.utcnow()
        
        # Create History Record (Time-series)
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

    # --- Market Share Logic ---

    @staticmethod
    def analyze_market_share(db: Session, competitor_id: uuid.UUID, tenant_id: uuid.UUID):
        """
        2-Step: Collect Signals -> Estimate Share.
        """
        # 1. Collect Signals (Mock)
        signals = [
            {"type": "traffic", "source": "similarweb", "score": 85},
            {"type": "mentions", "source": "google_search_api", "score": 40}
        ]
        
        # 2. Estimate Share & Trend
        # Logic: Traffic score / 1000 * weighting
        estimated_share = (signals[0]["score"] * 0.2) + (signals[1]["score"] * 0.1)
        trend = "up" if estimated_share > 10 else "stable"
        
        # 3. Store Snapshot
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
        
        # Update Main Record
        comp = db.query(Competitor).get(competitor_id)
        comp.market_share_est = estimated_share
        
        db.commit()
        return snapshot

    # --- Decision Engine (Price Comparison) ---

    @staticmethod
    def compare_prices(db: Session, my_price: float, product_keyword: str) -> Dict[str, Any]:
        """
        Returns a 'Decision Object' based on competitor data.
        """
        # 1. Find relevant competitor products
        # Simple ilike search for MVP
        competitor_products = db.query(CompetitorProduct).filter(
            CompetitorProduct.name.ilike(f"%{product_keyword}%"),
            CompetitorProduct.last_price.isnot(None)
        ).all()
        
        if not competitor_products:
            return {"status": "no_data", "decision": "Collect more data"}

        # 2. Calculate Stats
        prices = [float(p.last_price) for p in competitor_products]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        
        # 3. Decision Logic
        undercut_risk_score = 0
        margin_warning = False
        recommendation = "maintain"
        
        if my_price > avg_price * 1.1:
            undercut_risk_score = 80
            recommendation = "lower_price"
        elif my_price < min_price * 0.9:
            margin_warning = True
            recommendation = "raise_price" # Leaving money on table?
            undercut_risk_score = 10
            
        return {
            "market_avg": round(avg_price, 2),
            "market_min": round(min_price, 2),
            "my_price": my_price,
            "decision": {
                "undercut_risk_score": undercut_risk_score, # 0-100
                "margin_compression_warning": margin_warning, # Boolean
                "recommended_action": recommendation,
                "positioning": "premium" if my_price > avg_price else "budget"
            }
        }
