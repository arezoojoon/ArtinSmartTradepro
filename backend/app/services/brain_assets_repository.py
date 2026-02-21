"""
Phase 5 Brain Asset Repository
CRUD operations for asset databases with RLS support
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..models.brain_assets import (
    AssetArbitrageHistory, AssetSupplierReliability, AssetBuyerPaymentBehavior,
    AssetSeasonalityMatrix, BrainEngineRun, BrainDataSource, CulturalProfile,
    DemandTimeSeries, ArbitrageOutcome, BrainEngineType, BrainRunStatus
)

class BrainAssetRepository:
    """Repository for brain asset databases with RLS support"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Arbitrage History
    def create_arbitrage_history(self, tenant_id: UUID, data: Dict[str, Any]) -> AssetArbitrageHistory:
        """Create arbitrage history record"""
        arbitrage = AssetArbitrageHistory(
            tenant_id=tenant_id,
            product_key=data['product_key'],
            buy_market=data['buy_market'],
            sell_market=data['sell_market'],
            incoterms=data['incoterms'],
            buy_price=data['buy_price'],
            buy_currency=data['buy_currency'],
            sell_price=data['sell_price'],
            sell_currency=data['sell_currency'],
            freight_cost=data.get('freight_cost'),
            fx_rate=data.get('fx_rate'),
            estimated_margin_pct=data.get('estimated_margin_pct'),
            realized_margin_pct=data.get('realized_margin_pct'),
            outcome=data.get('outcome'),
            decision_reason=data.get('decision_reason'),
            data_used=data.get('data_used')
        )
        self.db.add(arbitrage)
        self.db.commit()
        self.db.refresh(arbitrage)
        return arbitrage
    
    def get_similar_arbitrage_deals(
        self, 
        tenant_id: UUID, 
        product_key: str, 
        buy_market: str, 
        sell_market: str,
        limit: int = 5
    ) -> List[AssetArbitrageHistory]:
        """Get similar past arbitrage deals"""
        return self.db.query(AssetArbitrageHistory).filter(
            AssetArbitrageHistory.tenant_id == tenant_id,
            AssetArbitrageHistory.product_key == product_key,
            or_(
                AssetArbitrageHistory.buy_market == buy_market,
                AssetArbitrageHistory.sell_market == sell_market
            )
        ).order_by(desc(AssetArbitrageHistory.created_at)).limit(limit).all()
    
    def list_arbitrage_history(
        self, 
        tenant_id: UUID, 
        product_key: Optional[str] = None,
        market: Optional[str] = None,
        outcome: Optional[ArbitrageOutcome] = None,
        limit: int = 50
    ) -> List[AssetArbitrageHistory]:
        """List arbitrage history with filters"""
        query = self.db.query(AssetArbitrageHistory).filter(
            AssetArbitrageHistory.tenant_id == tenant_id
        )
        
        if product_key:
            query = query.filter(AssetArbitrageHistory.product_key == product_key)
        
        if market:
            query = query.filter(
                or_(
                    AssetArbitrageHistory.buy_market == market,
                    AssetArbitrageHistory.sell_market == market
                )
            )
        
        if outcome:
            query = query.filter(AssetArbitrageHistory.outcome == outcome)
        
        return query.order_by(desc(AssetArbitrageHistory.created_at)).limit(limit).all()
    
    # Supplier Reliability
    def create_supplier_reliability(self, tenant_id: UUID, data: Dict[str, Any]) -> AssetSupplierReliability:
        """Create supplier reliability record"""
        supplier = AssetSupplierReliability(
            tenant_id=tenant_id,
            supplier_name=data['supplier_name'],
            supplier_country=data['supplier_country'],
            identifiers=data.get('identifiers'),
            on_time_rate=data.get('on_time_rate'),
            defect_rate=data.get('defect_rate'),
            dispute_count=data.get('dispute_count', 0),
            avg_lead_time_days=data.get('avg_lead_time_days'),
            reliability_score=data.get('reliability_score', 0),
            evidence=data.get('evidence')
        )
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier
    
    def get_supplier_reliability(
        self, 
        tenant_id: UUID, 
        supplier_name: str,
        supplier_country: str
    ) -> Optional[AssetSupplierReliability]:
        """Get supplier reliability by name and country"""
        return self.db.query(AssetSupplierReliability).filter(
            AssetSupplierReliability.tenant_id == tenant_id,
            AssetSupplierReliability.supplier_name == supplier_name,
            AssetSupplierReliability.supplier_country == supplier_country
        ).first()
    
    def list_suppliers_by_country(
        self, 
        tenant_id: UUID, 
        country: str,
        min_reliability: Optional[int] = None
    ) -> List[AssetSupplierReliability]:
        """List suppliers by country with optional reliability filter"""
        query = self.db.query(AssetSupplierReliability).filter(
            AssetSupplierReliability.tenant_id == tenant_id,
            AssetSupplierReliability.supplier_country == country
        )
        
        if min_reliability is not None:
            query = query.filter(AssetSupplierReliability.reliability_score >= min_reliability)
        
        return query.order_by(desc(AssetSupplierReliability.reliability_score)).all()
    
    # Buyer Payment Behavior
    def create_buyer_payment_behavior(self, tenant_id: UUID, data: Dict[str, Any]) -> AssetBuyerPaymentBehavior:
        """Create buyer payment behavior record"""
        buyer = AssetBuyerPaymentBehavior(
            tenant_id=tenant_id,
            buyer_country=data['buyer_country'],
            buyer_name=data.get('buyer_name'),
            segment=data.get('segment'),
            avg_payment_delay_days=data.get('avg_payment_delay_days'),
            default_rate=data.get('default_rate'),
            preferred_terms=data.get('preferred_terms'),
            payment_risk_score=data.get('payment_risk_score', 0),
            evidence=data.get('evidence')
        )
        self.db.add(buyer)
        self.db.commit()
        self.db.refresh(buyer)
        return buyer
    
    def get_buyer_payment_behavior(
        self, 
        tenant_id: UUID, 
        buyer_country: str,
        segment: Optional[str] = None
    ) -> List[AssetBuyerPaymentBehavior]:
        """Get buyer payment behavior by country and optional segment"""
        query = self.db.query(AssetBuyerPaymentBehavior).filter(
            AssetBuyerPaymentBehavior.tenant_id == tenant_id,
            AssetBuyerPaymentBehavior.buyer_country == buyer_country
        )
        
        if segment:
            query = query.filter(AssetBuyerPaymentBehavior.segment == segment)
        
        return query.order_by(desc(AssetBuyerPaymentBehavior.created_at)).all()
    
    # Seasonality Matrix
    def create_seasonality_matrix(self, tenant_id: UUID, data: Dict[str, Any]) -> AssetSeasonalityMatrix:
        """Create seasonality matrix record"""
        seasonality = AssetSeasonalityMatrix(
            tenant_id=tenant_id,
            product_key=data['product_key'],
            country=data['country'],
            season_key=data['season_key'],
            demand_index=data.get('demand_index'),
            price_index=data.get('price_index'),
            volatility_index=data.get('volatility_index'),
            data_used=data.get('data_used')
        )
        self.db.add(seasonality)
        self.db.commit()
        self.db.refresh(seasonality)
        return seasonality
    
    def get_seasonality_matrix(
        self, 
        tenant_id: UUID, 
        product_key: str,
        country: str
    ) -> List[AssetSeasonalityMatrix]:
        """Get seasonality matrix for product and country"""
        return self.db.query(AssetSeasonalityMatrix).filter(
            AssetSeasonalityMatrix.tenant_id == tenant_id,
            AssetSeasonalityMatrix.product_key == product_key,
            AssetSeasonalityMatrix.country == country
        ).order_by(AssetSeasonalityMatrix.season_key).all()
    
    # Brain Engine Runs
    def create_engine_run(self, tenant_id: UUID, data: Dict[str, Any]) -> BrainEngineRun:
        """Create brain engine run record"""
        run = BrainEngineRun(
            tenant_id=tenant_id,
            engine_type=data['engine_type'],
            input_payload=data['input_payload'],
            output_payload=data.get('output_payload'),
            explainability=data.get('explainability'),
            status=data['status'],
            error=data.get('error')
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
    
    def get_engine_runs(
        self, 
        tenant_id: UUID, 
        engine_type: Optional[BrainEngineType] = None,
        status: Optional[BrainRunStatus] = None,
        limit: int = 50
    ) -> List[BrainEngineRun]:
        """Get brain engine runs with filters"""
        query = self.db.query(BrainEngineRun).filter(
            BrainEngineRun.tenant_id == tenant_id
        )
        
        if engine_type:
            query = query.filter(BrainEngineRun.engine_type == engine_type)
        
        if status:
            query = query.filter(BrainEngineRun.status == status)
        
        return query.order_by(desc(BrainEngineRun.created_at)).limit(limit).all()
    
    def get_engine_run(self, tenant_id: UUID, run_id: UUID) -> Optional[BrainEngineRun]:
        """Get specific brain engine run"""
        return self.db.query(BrainEngineRun).filter(
            BrainEngineRun.tenant_id == tenant_id,
            BrainEngineRun.id == run_id
        ).first()
    
    # Brain Data Sources
    def create_data_source(self, tenant_id: UUID, data: Dict[str, Any]) -> BrainDataSource:
        """Create brain data source"""
        source = BrainDataSource(
            tenant_id=tenant_id,
            name=data['name'],
            type=data['type'],
            is_active=data.get('is_active', True),
            meta=data.get('meta')
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source
    
    def get_data_sources(self, tenant_id: UUID, active_only: bool = True) -> List[BrainDataSource]:
        """Get brain data sources"""
        query = self.db.query(BrainDataSource).filter(
            BrainDataSource.tenant_id == tenant_id
        )
        
        if active_only:
            query = query.filter(BrainDataSource.is_active == True)
        
        return query.order_by(BrainDataSource.name).all()
    
    # Cultural Profiles
    def create_cultural_profile(self, tenant_id: UUID, data: Dict[str, Any]) -> CulturalProfile:
        """Create cultural profile"""
        profile = CulturalProfile(
            tenant_id=tenant_id,
            country=data['country'],
            negotiation_style=data.get('negotiation_style'),
            do_dont=data.get('do_dont'),
            typical_terms=data.get('typical_terms')
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def get_cultural_profile(self, tenant_id: UUID, country: str) -> Optional[CulturalProfile]:
        """Get cultural profile by country"""
        return self.db.query(CulturalProfile).filter(
            CulturalProfile.tenant_id == tenant_id,
            CulturalProfile.country == country
        ).first()
    
    # Demand Time Series
    def create_demand_time_series(self, tenant_id: UUID, data: Dict[str, Any]) -> DemandTimeSeries:
        """Create demand time series record"""
        series = DemandTimeSeries(
            tenant_id=tenant_id,
            product_key=data['product_key'],
            country=data['country'],
            date=data['date'],
            demand_value=data.get('demand_value'),
            source_name=data['source_name'],
            data_used=data.get('data_used')
        )
        self.db.add(series)
        self.db.commit()
        self.db.refresh(series)
        return series
    
    def get_demand_time_series(
        self, 
        tenant_id: UUID, 
        product_key: str,
        country: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DemandTimeSeries]:
        """Get demand time series for product and country"""
        query = self.db.query(DemandTimeSeries).filter(
            DemandTimeSeries.tenant_id == tenant_id,
            DemandTimeSeries.product_key == product_key,
            DemandTimeSeries.country == country
        )
        
        if start_date:
            query = query.filter(DemandTimeSeries.date >= start_date)
        
        if end_date:
            query = query.filter(DemandTimeSeries.date <= end_date)
        
        return query.order_by(DemandTimeSeries.date).all()
    
    def get_demand_data_points_count(
        self, 
        tenant_id: UUID, 
        product_key: str,
        country: str
    ) -> int:
        """Get count of demand data points for product and country"""
        return self.db.query(DemandTimeSeries).filter(
            DemandTimeSeries.tenant_id == tenant_id,
            DemandTimeSeries.product_key == product_key,
            DemandTimeSeries.country == country
        ).count()
