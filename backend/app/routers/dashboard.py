from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from typing import Any
import datetime

from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.middleware.auth import get_current_active_user
from app.schemas.dashboard import DashboardMobileResponse

from app.models.billing import Wallet
from app.models.crm import CRMInvoice, CRMCompany
from app.models.brain import TradeOpportunity, RiskAssessment, MarketSignal
from app.models.hunter import HunterResult

router = APIRouter()

@router.get("/mobile", response_model=DashboardMobileResponse)
def get_mobile_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Data-driven Mobile Control Tower aggregation endpoint.
    Retrieves strict structs with Source, Timestamp, and Confidence for the 5 widgets.
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    if not tenant_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="User has no tenant association.")
    
    # 1. Liquidity (Wallet + CRM Invoices)
    wallet = db.query(Wallet).filter(Wallet.tenant_id == tenant_id).first()
    balance = float(wallet.balance) if wallet else 0.0
    
    # Calculate pending in/out (next 7 days)
    now = datetime.datetime.utcnow()
    next_week = now + datetime.timedelta(days=7)
    
    invoices_in = db.query(func.sum(CRMInvoice.amount)).filter(
        CRMInvoice.company_id.in_(
            select(CRMCompany.id).where(CRMCompany.tenant_id == current_tenant.id, CRMCompany.tags_json.contains("buyer"))
        ),
        CRMInvoice.status == "open",
        CRMInvoice.due_date <= next_week
    ).scalar() or 0.0
    
    invoices_out = db.query(func.sum(CRMInvoice.amount)).filter(
        CRMInvoice.company_id.in_(
            select(CRMCompany.id).where(CRMCompany.tenant_id == current_tenant.id, CRMCompany.tags_json.contains("supplier"))
        ),
        CRMInvoice.status == "open",
        CRMInvoice.due_date <= next_week
    ).scalar() or 0.0

    liquidity = {
        "balance": balance,
        "currency": wallet.currency if wallet else "USD",
        "pending_in": float(invoices_in),
        "pending_out": float(invoices_out),
        "dso": 24, # Stub calculation for DSO for now
        "source": "Wallet & CRM Invoices DB",
        "timestamp": now
    }

    # 2. Opportunities
    # Get active Top 3 opportunities
    db_opps = db.query(TradeOpportunity).filter(
        TradeOpportunity.tenant_id == current_tenant.id,
        TradeOpportunity.status == "new"
    ).order_by(TradeOpportunity.confidence_score.desc()).limit(3).all()
    
    opps_list = []
    for opp in db_opps:
        opps_list.append({
            "id": str(opp.id),
            "title": opp.title,
            "description": opp.description or f"Est. Profit: ${int(opp.estimated_profit or 0)}",
            "source": "AI Brain (Arbitrage Engine)",
            "timestamp": opp.created_at,
            "confidence": (opp.confidence_score or 0.9) * 100,
            "isInsufficientData": False
        })
    
    # Add an insufficient data fallback if empty
    if not opps_list:
        opps_list.append({
            "id": "insufficient-1",
            "title": "Arbitrage Detection",
            "source": "AI Brain",
            "timestamp": now,
            "confidence": 0,
            "isInsufficientData": True
        })

    # 3. Risks
    db_risks = db.query(RiskAssessment).filter(
        RiskAssessment.tenant_id == current_tenant.id,
        or_(RiskAssessment.risk_level == "High", RiskAssessment.risk_level == "Critical")
    ).order_by(RiskAssessment.timestamp.desc()).limit(3).all()

    risks_list = []
    for r in db_risks:
        risks_list.append({
            "id": str(r.id),
            "title": f"Risk: {r.origin_country} to {r.destination_country}",
            "description": f"Level: {r.risk_level} on {r.commodity}",
            "source": "Global Risk Engine",
            "timestamp": r.timestamp,
            "confidence": (float(r.risk_score or 0)) # Assuming 0-100 here
        })

    if not risks_list:
        risks_list.append({
            "id": "insufficient-risk",
            "title": "Active Trade Routes",
            "source": "Global Risk Engine",
            "timestamp": now,
            "confidence": 0,
            "isInsufficientData": True
        })


    # 4. Market Shocks
    db_shocks = db.query(MarketSignal).filter(
        MarketSignal.severity.in_(["high", "critical"])
    ).order_by(MarketSignal.created_at.desc()).limit(5).all()
    
    shocks_list = []
    for s in db_shocks:
        # Simple string manipulation for UI stub if trend not explicit
        trend = "down" if (s.sentiment_score and s.sentiment_score < 0) else "up"
        shocks_list.append({
            "id": str(s.id),
            "asset": s.impact_area or "Market",
            "change": s.headline[:15]+"..", # Quick mapping 
            "trend": trend,
            "source": "Bloomberg / Reuters API",
            "confidence": 95.0
        })

    # 5. New Leads (from latest CRMCompany additions + Hunter)
    db_leads = db.query(CRMCompany).filter(
        CRMCompany.tenant_id == current_tenant.id
    ).order_by(CRMCompany.id.desc()).limit(3).all() # Should ideally be created_at, but base model might not expose it easily

    leads_list = []
    for l in db_leads:
        leads_list.append({
            "id": str(l.id),
            "title": l.name,
            "description": f"{l.country or 'Unknown'} • {l.industry or 'Various'}",
            "source": "Hunter + TradeMap CRM Sync",
            "timestamp": now, # Placeholder until created_at is strictly selected
            "confidence": (l.risk_score or 80.0)
        })

    if not leads_list:
        leads_list.append({
            "id": "insufficient-lead",
            "title": "Recent Industry Scrapes",
            "source": "Hunter Engine",
            "timestamp": now,
            "confidence": 0,
            "isInsufficientData": True
        })

    return DashboardMobileResponse(
        liquidity=liquidity,
        opportunities=opps_list,
        risks=risks_list,
        shocks=shocks_list,
        leads=leads_list
    ) 

from app.schemas.dashboard import DashboardWebResponse
from app.models.crm import CRMPipeline, CRMDeal

@router.get("/web", response_model=DashboardWebResponse)
def get_web_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Data-driven Web App Dashboard aggregation endpoint.
    Retrieves Pipeline, Margin Matrix, Cash Flow Trends, Risk Heatmap, and Performance Snapshots.
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    if not tenant_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="User has no tenant association.")
        
    now = datetime.datetime.utcnow()

    # 1. Pipeline Summary Chart
    pipeline = db.query(CRMPipeline).filter(CRMPipeline.tenant_id == tenant_id).order_by(CRMPipeline.is_default.desc()).first()
    pipeline_list = []
    
    if pipeline and pipeline.stages:
        for stage in pipeline.stages:
            stage_id = stage.get("id")
            stage_name = stage.get("name")
            
            deals = db.query(CRMDeal).filter(
                CRMDeal.tenant_id == tenant_id,
                CRMDeal.pipeline_id == pipeline.id,
                CRMDeal.stage_id == stage_id,
                CRMDeal.status == "open"
            ).all()
            
            total_val = sum(d.value or 0.0 for d in deals)
            pipeline_list.append({
                "name": stage_name,
                "count": len(deals),
                "value": total_val
            })
    else:
        pipeline_list = [
            {"name": "Qualification", "count": 0, "value": 0.0},
            {"name": "Proposal", "count": 0, "value": 0.0},
            {"name": "Negotiation", "count": 0, "value": 0.0},
            {"name": "Closed Won", "count": 0, "value": 0.0}
        ]

    # 2. Margin Overview Matrix
    db_opps = db.query(TradeOpportunity).filter(
        TradeOpportunity.tenant_id == tenant_id,
        TradeOpportunity.status == "new"
    ).order_by(TradeOpportunity.confidence_score.desc()).limit(5).all()
    
    margin_matrix = []
    for opp in db_opps:
        margin_matrix.append({
            "product": opp.title,
            "origin": "Global",
            "destination": "Global",
            "net_margin": float(opp.estimated_profit or 0.0),
            "roi": float(opp.confidence_score or 0.0) * 100
        })

    # 3. Cash Flow & DSO Trends Graph
    cash_flow = []
    for i in range(5, -1, -1):
        month = now - datetime.timedelta(days=30*i)
        cash_flow.append({
            "period": month.strftime("%b"),
            "cash_in": 0.0,
            "cash_out": 0.0
        })

    # 4. Risk Heatmap
    db_risks = db.query(RiskAssessment).filter(
        RiskAssessment.tenant_id == tenant_id
    ).order_by(RiskAssessment.timestamp.desc()).limit(10).all()
    
    risk_heatmap = []
    for r in db_risks:
        risk_heatmap.append({
            "country": r.destination_country or r.origin_country,
            "category": r.commodity or "General",
            "score": int(r.risk_score or 0)
        })

    # 5. Supplier/Buyer Performance Snapshots
    db_companies = db.query(CRMCompany).filter(
        CRMCompany.tenant_id == tenant_id,
        CRMCompany.risk_score.isnot(None)
    ).order_by(CRMCompany.risk_score.desc()).limit(5).all()
    
    performance = []
    for c in db_companies:
        tags = c.tags_json or []
        comp_type = "buyer" if "buyer" in tags else "supplier" if "supplier" in tags else "other"
        performance.append({
            "id": str(c.id),
            "name": c.name,
            "type": comp_type,
            "score": float(c.risk_score or 80.0)
        })

    return DashboardWebResponse(
        pipeline=pipeline_list,
        margin_matrix=margin_matrix,
        cash_flow=cash_flow,
        risk_heatmap=risk_heatmap,
        performance=performance
    )
