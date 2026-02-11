from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import uuid
import logging
from app.models.financial import TradeScenario, CostComponent, RiskFactor

logger = logging.getLogger(__name__)

class FinancialService:
    """
    Service for Financial OS (Cost & Risk Engine).
    Handles Scenario Calculations, Landed Cost, and Risk-Adjusted Margin.
    """

    @staticmethod
    def calculate_scenario(db: Session, scenario_id: uuid.UUID) -> Dict[str, Any]:
        """
        Performs a full financial analysis of a scenario.
        Returns: { structure: {...}, landed_cost: 1200, net_margin: 15%, risk_adjusted: 12% }
        """
        scenario = db.query(TradeScenario).get(scenario_id)
        if not scenario:
            raise ValueError("Scenario not found")

        # 1. Calculate Landed Cost (Sum of all components)
        components = db.query(CostComponent).filter(
            CostComponent.scenario_id == scenario_id
        ).all()
        
        landed_cost_total = sum(c.amount for c in components)
        breakdown = {c.name: float(c.amount) for c in components}

        # 2. Revenue & Net Margin (Mock Revenue for now, typically comes from Deal)
        # Assuming we aim for the target margin stored in scenario
        # If Target Margin is 15%, then Revenue = Cost / (1 - 0.15)
        # This is a "Pricing Calculator" view. 
        # Alternatively, if Revenue is fixed, we calc Margin.
        # Let's assume a mock Revenue based on Cost + 20% Markup for simulation
        revenue = float(landed_cost_total) * 1.20 
        net_profit = revenue - float(landed_cost_total)
        net_margin_percent = (net_profit / revenue) * 100 if revenue else 0

        # 3. Risk Adjustments
        risks = db.query(RiskFactor).filter(
            RiskFactor.scenario_id == scenario_id
        ).all()
        
        # Risk Impact Calculation:
        # Risk Cost = (Impact % of Revenue) * Probability
        # e.g. FX Risk: 5% impact * 50% probability = 2.5% effective margin reduction
        
        total_risk_penalty_percent = 0
        risk_breakdown = []
        
        for r in risks:
            # Expected Value of Risk = Probability * Impact
            ev_percent = float(r.probability) * float(r.impact_percent)
            total_risk_penalty_percent += ev_percent
            
            risk_breakdown.append({
                "type": r.factor_type,
                "probability": float(r.probability),
                "impact": float(r.impact_percent),
                "expected_penalty": round(ev_percent, 2)
            })

        risk_adjusted_margin_percent = net_margin_percent - total_risk_penalty_percent

        return {
            "scenario_name": scenario.name,
            "currency": scenario.currency,
            "economics": {
                "revenue": round(revenue, 2),
                "landed_cost": round(float(landed_cost_total), 2),
                "net_profit": round(net_profit, 2),
                "net_margin_percent": round(net_margin_percent, 2)
            },
            "risk_analysis": {
                "risk_penalty_percent": round(total_risk_penalty_percent, 2),
                "risk_adjusted_margin_percent": round(risk_adjusted_margin_percent, 2),
                "factors": risk_breakdown
            },
            "cost_structure": breakdown
        }

    @staticmethod
    def clone_scenario(db: Session, source_id: uuid.UUID, new_name: str) -> TradeScenario:
        """
        Clones a scenario (e.g. Base -> Pessimistic) for A/B testing.
        """
        source = db.query(TradeScenario).get(source_id)
        if not source:
            raise ValueError("Source scenario not found")
            
        new_scenario = TradeScenario(
            tenant_id=source.tenant_id,
            name=new_name,
            currency=source.currency,
            target_margin_percent=source.target_margin_percent,
            status="active"
        )
        db.add(new_scenario)
        db.flush() # Generate ID
        
        # Clone Costs
        for c in source.cost_components:
            db.add(CostComponent(
                scenario_id=new_scenario.id,
                name=c.name,
                cost_type=c.cost_type,
                amount=c.amount,
                currency=c.currency
            ))
            
        # Clone Risks
        for r in source.risk_factors:
            db.add(RiskFactor(
                scenario_id=new_scenario.id,
                factor_type=r.factor_type,
                probability=r.probability,
                impact_percent=r.impact_percent,
                mitigation_cost=r.mitigation_cost
            ))
            
        db.commit()
        db.refresh(new_scenario)
        return new_scenario
