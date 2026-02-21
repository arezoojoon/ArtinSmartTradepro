"""
Phase 5 Arbitrage Engine v1
Deterministic arbitrage analysis with similar past deals
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.brain_assets import AssetArbitrageHistory, ArbitrageOutcome
from ..services.brain_assets_repository import BrainAssetRepository
from ..services.brain_registry import BrainEngineRegistry, BrainEngineValidator, make_data_used_item
from ..schemas.brain import (
    ArbitrageInput, ArbitrageOutput, ArbitrageOpportunityCard, 
    SimilarDeal, ExplainabilityBundle
)

class ArbitrageEngine:
    """
    Deterministic arbitrage analysis engine
    Computes margins, finds similar deals, and provides explainable insights
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = BrainAssetRepository(db)
        self.registry = BrainEngineRegistry(db)
        self.validator = BrainEngineValidator()
    
    def run_analysis(self, tenant_id: UUID, input_data: ArbitrageInput) -> ArbitrageOutput:
        """
        Run complete arbitrage analysis
        
        Args:
            tenant_id: Tenant ID for RLS
            input_data: Arbitrage analysis input
            
        Returns:
            ArbitrageOutput with opportunity card and similar deals
        """
        try:
            # Validate input
            validation_result = self._validate_input(input_data)
            if not validation_result[0]:
                return self._create_insufficient_data_response(
                    tenant_id, input_data, validation_result[1]
                )
            
            # Compute arbitrage analysis
            analysis_result = self._compute_arbitrage(tenant_id, input_data)
            
            # Find similar past deals
            similar_deals = self._find_similar_deals(tenant_id, input_data)
            
            # Create explainability bundle
            explainability = self._create_explainability_bundle(
                tenant_id, input_data, analysis_result, similar_deals
            )
            
            # Create opportunity card
            opportunity_card = self._create_opportunity_card(analysis_result)
            
            # Save engine run
            output_payload = {
                "opportunity_card": opportunity_card.dict(),
                "similar_deals": [deal.dict() for deal in similar_deals],
                "analysis_result": analysis_result
            }
            
            self.registry.create_successful_run(
                tenant_id,
                "arbitrage",
                input_data.dict(),
                output_payload,
                explainability
            )
            
            return ArbitrageOutput(
                status="success",
                opportunity_card=opportunity_card,
                similar_deals=similar_deals,
                explainability=explainability
            )
            
        except Exception as e:
            # Create failed run
            error_data = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.registry.create_failed_run(
                tenant_id,
                "arbitrage",
                input_data.dict(),
                error_data
            )
            
            raise
    
    def _validate_input(self, input_data: ArbitrageInput) -> Tuple[bool, List[str]]:
        """Validate arbitrage input data"""
        missing_fields = []
        
        # Check required fields
        required_fields = [
            'product_key', 'buy_market', 'sell_market', 
            'buy_price', 'buy_currency', 'sell_price', 'sell_currency'
        ]
        
        is_valid, missing = self.validator.validate_required_fields(
            input_data.dict(), required_fields
        )
        missing_fields.extend(missing)
        
        # Check numeric fields
        numeric_fields = ['buy_price', 'sell_price', 'freight_cost']
        is_valid_numeric, invalid_numeric = self.validator.validate_numeric_fields(
            input_data.dict(), numeric_fields
        )
        missing_fields.extend(invalid_numeric)
        
        # Check currency codes
        currency_fields = ['buy_currency', 'sell_currency']
        is_valid_currency, invalid_currency = self.validator.validate_currency_codes(
            input_data.dict(), currency_fields
        )
        missing_fields.extend(invalid_currency)
        
        return (len(missing_fields) == 0), missing_fields
    
    def _compute_arbitrage(self, tenant_id: UUID, input_data: ArbitrageInput) -> Dict[str, Any]:
        """
        Compute arbitrage analysis with deterministic calculations
        
        Returns:
            Dict with computed values and assumptions
        """
        # Base currency for normalization (USD)
        base_currency = "USD"
        
        # Get FX rates (use provided or default to 1.0)
        fx_rates = input_data.fx_rates or {}
        
        # Normalize buy price to USD
        if input_data.buy_currency == base_currency:
            buy_price_usd = input_data.buy_price
        else:
            fx_key = f"{input_data.buy_currency}_{base_currency}"
            buy_fx_rate = fx_rates.get(fx_key, 1.0)
            buy_price_usd = input_data.buy_price * buy_fx_rate
        
        # Normalize sell price to USD
        if input_data.sell_currency == base_currency:
            sell_price_usd = input_data.sell_price
        else:
            fx_key = f"{input_data.sell_currency}_{base_currency}"
            sell_fx_rate = fx_rates.get(fx_key, 1.0)
            sell_price_usd = input_data.sell_price * sell_fx_rate
        
        # Add freight cost if provided
        total_freight_cost = input_data.freight_cost or 0.0
        
        # Add fees if provided
        total_fees = 0.0
        if input_data.fees:
            for fee in input_data.fees:
                fee_amount = fee.get('amount', 0)
                fee_currency = fee.get('currency', base_currency)
                
                if fee_currency != base_currency:
                    fx_key = f"{fee_currency}_{base_currency}"
                    fee_fx_rate = fx_rates.get(fx_key, 1.0)
                    fee_amount = fee_amount * fee_fx_rate
                
                total_fees += fee_amount
        
        # Calculate total cost and revenue
        total_cost_usd = buy_price_usd + total_freight_cost + total_fees
        total_revenue_usd = sell_price_usd
        
        # Calculate margin
        if total_cost_usd > 0:
            margin_pct = ((total_revenue_usd - total_cost_usd) / total_cost_usd) * 100
        else:
            margin_pct = 0.0
        
        # Calculate confidence
        confidence = self._calculate_confidence(input_data)
        
        return {
            "buy_price_usd": buy_price_usd,
            "sell_price_usd": sell_price_usd,
            "total_cost_usd": total_cost_usd,
            "total_revenue_usd": total_revenue_usd,
            "total_freight_cost": total_freight_cost,
            "total_fees": total_fees,
            "estimated_margin_pct": margin_pct,
            "base_currency": base_currency,
            "confidence": confidence,
            "assumptions": self._get_assumptions(input_data),
            "target_margin_met": (
                input_data.target_margin_pct is None or 
                margin_pct >= input_data.target_margin_pct
            )
        }
    
    def _calculate_confidence(self, input_data: ArbitrageInput) -> float:
        """
        Calculate confidence score based on input completeness
        
        Rules:
        - Start at 0.3
        - +0.2 if freight provided
        - +0.2 if fx provided
        - +0.2 if fees provided
        - Cap at 0.9
        """
        confidence = 0.3
        
        if input_data.freight_cost is not None:
            confidence += 0.2
        
        if input_data.fx_rates is not None and len(input_data.fx_rates) > 0:
            confidence += 0.2
        
        if input_data.fees is not None and len(input_data.fees) > 0:
            confidence += 0.2
        
        return min(confidence, 0.9)
    
    def _get_assumptions(self, input_data: ArbitrageInput) -> List[str]:
        """Get list of assumptions made during calculation"""
        assumptions = ["Base currency set to USD"]
        
        if not input_data.fx_rates:
            assumptions.append("FX rates not provided, using 1.0 (no conversion)")
        
        if not input_data.freight_cost:
            assumptions.append("Freight cost not provided, using 0.0")
        
        if not input_data.fees:
            assumptions.append("Additional fees not provided, using 0.0")
        
        return assumptions
    
    def _find_similar_deals(self, tenant_id: UUID, input_data: ArbitrageInput) -> List[SimilarDeal]:
        """Find similar past arbitrage deals"""
        similar_records = self.repo.get_similar_arbitrage_deals(
            tenant_id,
            input_data.product_key,
            input_data.buy_market,
            input_data.sell_market,
            limit=5
        )
        
        similar_deals = []
        for record in similar_records:
            deal = SimilarDeal(
                id=record.id,
                product_key=record.product_key,
                buy_market=record.buy_market,
                sell_market=record.sell_market,
                estimated_margin_pct=record.estimated_margin_pct,
                realized_margin_pct=record.realized_margin_pct,
                outcome=record.outcome,
                created_at=record.created_at
            )
            similar_deals.append(deal)
        
        return similar_deals
    
    def _create_opportunity_card(self, analysis_result: Dict[str, Any]) -> ArbitrageOpportunityCard:
        """Create opportunity card with key insights"""
        margin_pct = analysis_result["estimated_margin_pct"]
        confidence = analysis_result["confidence"]
        
        # Determine key drivers
        key_drivers = []
        if margin_pct > 10:
            key_drivers.append(f"High margin opportunity ({margin_pct:.1f}%)")
        elif margin_pct > 5:
            key_drivers.append(f"Moderate margin ({margin_pct:.1f}%)")
        else:
            key_drivers.append(f"Low margin ({margin_pct:.1f}%)")
        
        if analysis_result["total_freight_cost"] > 0:
            key_drivers.append(f"Freight cost: ${analysis_result['total_freight_cost']:.2f}")
        
        if analysis_result["total_fees"] > 0:
            key_drivers.append(f"Additional fees: ${analysis_result['total_fees']:.2f}")
        
        # Generate next actions
        next_actions = []
        if margin_pct > 5:
            next_actions.append("Request detailed quote from supplier")
            next_actions.append("Verify HS code classification")
            next_actions.append("Confirm freight costs")
        else:
            next_actions.append("Negotiate better buy price")
            next_actions.append("Review cost structure")
            next_actions.append("Consider alternative markets")
        
        # Add risk factors
        risk_factors = []
        if confidence < 0.7:
            risk_factors.append("Low confidence due to missing cost data")
        
        if not analysis_result["target_margin_met"]:
            risk_factors.append("Below target margin threshold")
        
        return ArbitrageOpportunityCard(
            estimated_margin_pct=margin_pct,
            key_drivers=key_drivers,
            next_actions=next_actions,
            risk_factors=risk_factors
        )
    
    def _create_explainability_bundle(
        self,
        tenant_id: UUID,
        input_data: ArbitrageInput,
        analysis_result: Dict[str, Any],
        similar_deals: List[SimilarDeal]
    ) -> ExplainabilityBundle:
        """Create comprehensive explainability bundle"""
        
        # Data used
        data_used = []
        
        # Add input data source
        data_used.append(make_data_used_item(
            source_name="user_input",
            dataset="arbitrage_analysis_input",
            coverage=f"{input_data.product_key} {input_data.buy_market}->{input_data.sell_market}",
            confidence=1.0
        ))
        
        # Add similar deals data source if available
        if similar_deals:
            data_used.append(make_data_used_item(
                source_name="asset_arbitrage_history",
                dataset="similar_past_deals",
                coverage=f"{len(similar_deals)} similar deals",
                record_count=len(similar_deals),
                confidence=0.8
            ))
        
        # Assumptions
        assumptions = analysis_result["assumptions"]
        
        # Confidence calculation
        confidence = analysis_result["confidence"]
        confidence_rationale = f"Base confidence 0.3 + input completeness = {confidence:.1f}"
        
        # Action plan
        action_plan = []
        if analysis_result["estimated_margin_pct"] > 5:
            action_plan.extend([
                "Proceed with supplier RFQ",
                "Verify all cost assumptions",
                "Check similar deal outcomes"
            ])
        else:
            action_plan.extend([
                "Improve cost data quality",
                "Negotiate better terms",
                "Explore alternative markets"
            ])
        
        # Limitations
        limitations = [
            "Analysis based on provided cost estimates",
            "FX rates may be outdated",
            "Market conditions may have changed"
        ]
        
        if not similar_deals:
            limitations.append("No similar past deals found for validation")
        
        return ExplainabilityBundle(
            data_used=data_used,
            assumptions=assumptions,
            confidence=confidence,
            confidence_rationale=confidence_rationale,
            action_plan=action_plan,
            limitations=limitations,
            computation_method="Deterministic margin calculation with USD normalization",
            missing_fields=[]
        )
    
    def _create_insufficient_data_response(
        self,
        tenant_id: UUID,
        input_data: ArbitrageInput,
        missing_fields: List[str]
    ) -> ArbitrageOutput:
        """Create insufficient data response"""
        suggested_steps = [
            f"Provide missing field: {field}" for field in missing_fields
        ]
        
        # Create insufficient data run
        self.registry.create_insufficient_data_run(
            tenant_id,
            "arbitrage",
            input_data.dict(),
            missing_fields,
            suggested_steps
        )
        
        return ArbitrageOutput(
            status="insufficient_data",
            explainability=ExplainabilityBundle(
                data_used=[],
                assumptions=[f"Missing required fields: {', '.join(missing_fields)}"],
                confidence=0.0,
                confidence_rationale="Insufficient data for computation",
                action_plan=suggested_steps,
                limitations=["Insufficient data"],
                computation_method="None - insufficient data",
                missing_fields=missing_fields
            )
        )
