from sqlalchemy.orm import Session
from app.models.climate import ClimateRisk
from app.models.financial import RiskFactor
import datetime
import uuid

class ClimateService:
    """
    Predicts disruption based on weather/geopolitical events.
    """

    @staticmethod
    def get_active_risks(db: Session):
        """
        Returns all currently valid climate risks.
        """
        now = datetime.datetime.utcnow()
        return db.query(ClimateRisk).filter(
            (ClimateRisk.valid_until == None) | (ClimateRisk.valid_until >= now)
        ).all()

    @staticmethod
    def assess_route_risk(db: Session, route_name: str, financial_scenario_id: uuid.UUID):
        """
        Checks if a route (e.g., "China-Dubai") intersects with known risks.
        If yes, it creates a RiskFactor in the Financial Engine.
        """
        # Mock Logic: Simple string matching
        risks = ClimateService.get_active_risks(db)
        
        impact_found = False
        for risk in risks:
            if risk.region.lower() in route_name.lower():
                # Create Financial Risk Factor
                new_factor = RiskFactor(
                    scenario_id=financial_scenario_id,
                    factor_type=f"Climate: {risk.risk_type.title()}",
                    probability=0.8 if risk.severity == "high" else 0.4,
                    impact_percent=10.0 if risk.severity == "high" else 3.0,
                    description=f"Automated risk detected from {risk.region}"
                )
                db.add(new_factor)
                impact_found = True
        
        if impact_found:
            db.commit()
        
        return impact_found
