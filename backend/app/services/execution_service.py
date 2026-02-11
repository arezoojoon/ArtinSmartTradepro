from sqlalchemy.orm import Session
from app.models.execution import OutreachQueue, TradeOpportunity
from app.models.financial import TradeScenario, CostComponent
from app.models.sourcing import Supplier
from app.models.crm import CRMCompany
import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

class ExecutionService:
    """
    Execution Layer: Automated Outreach & Trade Orchestration.
    """
    
    @staticmethod
    def queue_outreach(db: Session, tenant_id, contact_id, channel, content, campaign_id=None, scheduled_for=None):
        """Add a message to the execution queue."""
        queue_item = OutreachQueue(
            tenant_id=tenant_id,
            contact_id=contact_id,
            campaign_id=campaign_id,
            channel=channel,
            content_payload=content,
            scheduled_for=scheduled_for or datetime.datetime.utcnow(),
            status="pending"
        )
        db.add(queue_item)
        db.commit()
        return queue_item

    @staticmethod
    def process_queue(db: Session):
        """
        Worker method to process pending items.
        (Stub implementation for audit verification)
        """
        now = datetime.datetime.utcnow()
        pending = db.query(OutreachQueue).filter(
            OutreachQueue.status == "pending",
            OutreachQueue.scheduled_for <= now
        ).limit(50).all()
        
        for item in pending:
            try:
                # STUB: Call Email/WhatsApp Provider
                logger.info(f"Executing outreach {item.id} via {item.channel}")
                
                item.status = "sent"
                item.sent_at = datetime.datetime.utcnow()
            except Exception as e:
                item.status = "failed"
                item.error_log = str(e)
            
        db.commit()

    # --- Trade Opportunity Logic (Phase 10) ---

    @staticmethod
    def create_opportunity(db: Session, tenant_id: uuid.UUID, title: str, buyer_id: uuid.UUID, supplier_id: uuid.UUID) -> TradeOpportunity:
        """
        Creates a new Trade Opportunity and auto-generates a Financial Scenario.
        """
        # 1. Create the Opportunity
        opp = TradeOpportunity(
            tenant_id=tenant_id,
            title=title,
            buyer_id=buyer_id,
            supplier_id=supplier_id,
            stage="identified",
            win_probability=50
        )
        db.add(opp)
        db.flush()

        # 2. Auto-Generate Financial Scenario (Base Case)
        # We clone a "template" or create a fresh one based on Supplier/Buyer data
        scenario = TradeScenario(
            tenant_id=tenant_id,
            name=f"Scenario for {title}",
            status="active",
            currency="USD",
            target_margin_percent=15.0
        )
        db.add(scenario)
        db.flush()

        # 3. Add Default Cost Components (Stubbed logic for now)
        # In a real system, we'd lookup Freight Rates here
        default_costs = [
            CostComponent(scenario_id=scenario.id, name="Freight Estimate", amount=2500, cost_type="variable"),
            CostComponent(scenario_id=scenario.id, name="Insurance", amount=150, cost_type="variable"),
            CostComponent(scenario_id=scenario.id, name="Customs Clearance", amount=500, cost_type="fixed")
        ]
        db.add_all(default_costs)

        # 4. Link & Recalculate Probability
        opp.financial_scenario_id = scenario.id
        opp.win_probability = ExecutionService.calculate_win_probability(db, opp)
        
        db.commit()
        db.refresh(opp)
        return opp

    @staticmethod
    def calculate_win_probability(db: Session, opp: TradeOpportunity) -> int:
        """
        Calculates Win Probability based on:
        - Supplier Reliability (Sourcing)
        - Buyer Credit/Profile (CRM) -> Mocked as 80 for now
        """
        score = 50 # Base

        if opp.supplier_id:
            supplier = db.query(Supplier).get(opp.supplier_id)
            if supplier:
                # Reliability > 80 adds points
                if supplier.reliability_score >= 80:
                    score += 10
                elif supplier.reliability_score < 50:
                    score -= 10
        
        # Mock Buyer Logic (CRM Buyer Credit Score not yet implemented)
        # if opp.buyer.credit_score > 700: score += 10

        return min(max(score, 0), 100)
