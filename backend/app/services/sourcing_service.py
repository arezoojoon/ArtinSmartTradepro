from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import uuid
import datetime
import logging
from app.models.sourcing import Supplier, RFQ, SupplierQuote, SupplierIssue

logger = logging.getLogger(__name__)

class SupplierIntelligenceService:
    """
    Service for Sourcing Intelligence (Supplier OS).
    Handles Supplier Scoring, RFQ Management, and Reliability Analysis.
    """

    # --- Explainable Scoring Engine ---

    @staticmethod
    def calculate_reliability_score(db: Session, supplier_id: uuid.UUID) -> Dict[str, Any]:
        """
        Calculates a reliability score breakdown based on documented issues.
        Returns: { overall: 85, on_time: 90, quality: 80, explanations: [...] }
        """
        supplier = db.query(Supplier).get(supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")

        # 1. Fetch Issues
        issues = db.query(SupplierIssue).filter(
            SupplierIssue.supplier_id == supplier_id
        ).all()

        # 2. Base Scores (Start at 100)
        scores = {
            "on_time": 100,
            "quality": 100, 
            "communication": 100,
            "documentation": 100
        }
        explanations = []

        # 3. Deduct Points per Issue
        for issue in issues:
            deduction = issue.severity * 5  # e.g., Severity 1 = -5, Severity 5 = -25
            
            if issue.issue_type == "delay":
                scores["on_time"] = max(0, scores["on_time"] - deduction)
                explanations.append(f"Delay event ({issue.created_at.date()}): -{deduction} pts to On-Time")
            elif issue.issue_type == "quality":
                scores["quality"] = max(0, scores["quality"] - deduction)
                explanations.append(f"Quality event ({issue.created_at.date()}): -{deduction} pts to Quality")
            elif issue.issue_type == "communication":
                scores["communication"] = max(0, scores["communication"] - deduction)
                explanations.append(f"Comm. issue ({issue.created_at.date()}): -{deduction} pts")
            elif issue.issue_type == "documents":
                scores["documentation"] = max(0, scores["documentation"] - deduction)
                explanations.append(f"Doc error ({issue.created_at.date()}): -{deduction} pts")

        # 4. Calculate Overall Weighted Score
        # Weights: On-Time (40%), Quality (40%), Comm (10%), Docs (10%)
        overall = (
            (scores["on_time"] * 0.4) +
            (scores["quality"] * 0.4) +
            (scores["communication"] * 0.1) +
            (scores["documentation"] * 0.1)
        )
        
        # Update Supplier Record
        supplier.reliability_score = overall
        db.commit()

        return {
            "overall_score": round(overall, 1),
            "breakdown": scores,
            "explanations": explanations
        }

    # --- Lead Time Prediction ---

    @staticmethod
    def predict_lead_time(db: Session, supplier_id: uuid.UUID, route_code: str = "default") -> int:
        """
        Predicts lead time based on supplier history + route buffer.
        """
        supplier = db.query(Supplier).get(supplier_id)
        # Mock logic v1: Base 30 days
        base_lead_time = 30
        
        # Add capacity factor (if capacity is low, lead time increases)
        # capacity_index 0-100 (100 is full capacity available? No, usually 100 means good.)
        # Let's say capacity_index 100 = fast, 0 = slow/full.
        capacity_penalty = 0
        if supplier.capacity_index < 50:
            capacity_penalty = 15 # +2 weeks if busy
            
        # Route buffer
        route_buffer = 0
        if route_code == "sea_remote":
            route_buffer = 30
        elif route_code == "air_express":
            route_buffer = -20
            
        return base_lead_time + capacity_penalty + route_buffer

    # --- Actionable Intelligence ---
    
    @staticmethod
    def compare_quotes(db: Session, rfq_id: uuid.UUID) -> List[Dict]:
        """
        Compares quotes for an RFQ, normalizing for Incoterms and Risk.
        """
        quotes = db.query(SupplierQuote).filter(SupplierQuote.rfq_id == rfq_id).all()
        comparison = []
        
        for q in quotes:
            # Get reliability for context
            reliability = db.query(Supplier.reliability_score).filter(Supplier.id == q.supplier_id).scalar() or 50
            
            # Simple score: Price vs Reliability
            # Lower price is better, Higher reliability is better.
            # Value Score = Reliability / Price (normalized) - simplistic
            
            comparison.append({
                "quote_id": str(q.id),
                "supplier_name": q.supplier.name,
                "price": float(q.unit_price),
                "incoterm": q.incoterm,
                "lead_time": q.lead_time_days,
                "reliability_score": float(reliability),
                "risk_adjusted_rank": "A" if reliability > 80 else "B" if reliability > 50 else "C"
            })
            
        # Sort by price (asc) for now
        comparison.sort(key=lambda x: x["price"])
        return comparison
