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

from app.models.billing import Wallet, WalletTransaction
from app.models.crm import CRMInvoice, CRMCompany
from sqlalchemy import func as sqla_func

import logging
logger = logging.getLogger(__name__)
# Try to import BrainEngineRun, but handle gracefully if it doesn't exist
try:
    from app.models.brain import BrainEngineRun
except ImportError:
    BrainEngineRun = None
from app.models.hunter_phase4 import HunterLead

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
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Initialize response data
    liquidity = {
        "pending_in": 0,
        "pending_out": 0,
        "dso": 45,
        "source": "Wallet Service",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "confidence": 0.95
    }
    
    opportunities = []
    risks = []
    shocks = []
    leads = []
    
    # 1. Today's Opportunities from Brain Engine
    try:
        # Get recent arbitrage opportunities
        if BrainEngineRun is not None:
            brain_runs = db.query(BrainEngineRun).filter(
                BrainEngineRun.tenant_id == tenant_id,
                BrainEngineRun.engine_type == "arbitrage",
                BrainEngineRun.status == "success",
                BrainEngineRun.created_at >= datetime.datetime.utcnow() - datetime.timedelta(days=1)
            ).order_by(BrainEngineRun.created_at.desc()).limit(3).all()
            
            for run in brain_runs:
                if run.output_payload and "opportunity_card" in run.output_payload:
                    opp = run.output_payload["opportunity_card"]
                    opportunities.append({
                        "id": str(run.id),
                        "title": f"{opp.get('product', 'Unknown')} Arbitrage",
                        "description": f"Buy: {opp.get('buy_market')} @ ${opp.get('buy_price', 0)}, Sell: {opp.get('sell_market')} @ ${opp.get('sell_price', 0)}",
                        "source": "Brain Arbitrage Engine",
                        "timestamp": run.created_at.isoformat(),
                        "confidence": opp.get('confidence', 0.8),
                        "isInsufficientData": False
                    })
        else:
            # BrainEngineRun model not available, add placeholder
            opportunities.append({
                "id": "model-unavailable",
                "title": "Brain Engine Unavailable",
                "description": "Brain Engine model is currently unavailable",
                "source": "Brain Engine",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "confidence": 0.0,
                "isInsufficientData": True
            })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching opportunities: {e}")
        # Add insufficient data placeholder
        opportunities.append({
            "id": "insufficient-data",
            "title": "Insufficient Data",
            "description": "Not enough market data to generate opportunities",
            "source": "Brain Engine",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "confidence": 0.0,
            "isInsufficientData": True
        })
    
    # 2. Risk Alerts from Risk Engine
    try:
        if BrainEngineRun is not None:
            risk_runs = db.query(BrainEngineRun).filter(
                BrainEngineRun.tenant_id == tenant_id,
                BrainEngineRun.engine_type == "risk",
                BrainEngineRun.status == "success",
                BrainEngineRun.created_at >= datetime.datetime.utcnow() - datetime.timedelta(days=1)
            ).order_by(BrainEngineRun.created_at.desc()).limit(3).all()
            
            for run in risk_runs:
                if run.output_payload and "risk_assessment" in run.output_payload:
                    risk = run.output_payload["risk_assessment"]
                    if risk.get("overall_risk_level") in ["high", "critical"]:
                        risks.append({
                            "id": str(run.id),
                            "title": f"High Risk: {risk.get('primary_risk', 'Unknown')}",
                            "description": risk.get("recommendation", "Review required"),
                            "source": "Brain Risk Engine",
                            "timestamp": run.created_at.isoformat(),
                            "confidence": risk.get('confidence', 0.8),
                            "isInsufficientData": False
                        })
    except Exception as e:
        logger.error(f"Error fetching risks: {e}")
    
    # 3. Market Shocks — empty until external market data API is integrated
    shocks = []
    
    # 4. New Leads from Hunter
    try:
        # Get recent scored leads
        hunter_leads = db.query(HunterLead).filter(
            HunterLead.tenant_id == tenant_id,
            HunterLead.status == "qualified",
            HunterLead.created_at >= datetime.datetime.utcnow() - datetime.timedelta(days=7)
        ).order_by(HunterLead.score_total.desc()).limit(3).all()
        
        for lead in hunter_leads:
            leads.append({
                "id": str(lead.id),
                "title": lead.primary_name,
                "description": f"{lead.country} - Score: {lead.score_total}",
                "source": "Hunter Lead Generation",
                "timestamp": lead.created_at.isoformat(),
                "confidence": min(lead.score_total / 100, 1.0),
                "isInsufficientData": False
            })
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
    
    # 5. Cash Flow Status from Wallet
    try:
        # Calculate pending in/out from invoices and wallet
        wallet = db.query(Wallet).filter(Wallet.tenant_id == tenant_id).first()
        
        if wallet:
            # Pending In: sum of open invoices (money owed to us)
            pending_in = db.query(sqla_func.coalesce(sqla_func.sum(CRMInvoice.amount), 0)).filter(
                CRMInvoice.tenant_id == tenant_id,
                CRMInvoice.status == "open"
            ).scalar() or 0
            liquidity["pending_in"] = float(pending_in)

            # Pending Out: sum of overdue invoices
            pending_out = db.query(sqla_func.coalesce(sqla_func.sum(CRMInvoice.amount), 0)).filter(
                CRMInvoice.tenant_id == tenant_id,
                CRMInvoice.status == "overdue"
            ).scalar() or 0
            liquidity["pending_out"] = float(pending_out)

            # DSO: average days between issued and paid
            paid_invoices = db.query(CRMInvoice).filter(
                CRMInvoice.tenant_id == tenant_id,
                CRMInvoice.paid_date != None
            ).order_by(CRMInvoice.paid_date.desc()).limit(50).all()
            if paid_invoices:
                total_days = sum((inv.paid_date - inv.issued_date).days for inv in paid_invoices if inv.issued_date)
                liquidity["dso"] = round(total_days / len(paid_invoices), 1)
            else:
                liquidity["dso"] = 0
    except Exception as e:
        logger.error(f"Error fetching liquidity: {e}")
    
    return DashboardMobileResponse(
        liquidity=liquidity,
        opportunities=opportunities,
        risks=risks,
        shocks=shocks,
        leads=leads
    ) 

from app.schemas.dashboard import DashboardWebResponse
from app.models.crm import CRMPipeline, CRMDeal

try:
    from app.models.phase5 import AssetArbitrageHistory
except ImportError:
    AssetArbitrageHistory = None

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

    # 2. Margin Overview Matrix from real arbitrage history
    margin_matrix = []
    if AssetArbitrageHistory:
        arb_records = db.query(AssetArbitrageHistory).filter(
            AssetArbitrageHistory.tenant_id == tenant_id,
            AssetArbitrageHistory.created_at >= now - datetime.timedelta(days=30)
        ).order_by(AssetArbitrageHistory.created_at.desc()).limit(10).all()
        for rec in arb_records:
            margin_matrix.append({
                "product": rec.product_key or "Unknown",
                "origin": rec.buy_market or "N/A",
                "destination": rec.sell_market or "N/A",
                "net_margin": float(rec.estimated_margin_pct) if rec.estimated_margin_pct else 0,
                "roi": float(rec.realized_margin_pct) if rec.realized_margin_pct else 0
            })

    # 3. Cash Flow & DSO Trends from real wallet transactions
    cash_flow = []
    wallet = db.query(Wallet).filter(Wallet.tenant_id == tenant_id).first()
    for i in range(5, -1, -1):
        period_start = now - datetime.timedelta(days=30*i)
        period_end = period_start + datetime.timedelta(days=30)
        cash_in_val = 0.0
        cash_out_val = 0.0
        if wallet:
            credits = db.query(sqla_func.coalesce(sqla_func.sum(WalletTransaction.amount), 0)).filter(
                WalletTransaction.wallet_id == wallet.id,
                WalletTransaction.type == "credit",
                WalletTransaction.status == "completed",
                WalletTransaction.created_at >= period_start,
                WalletTransaction.created_at < period_end
            ).scalar() or 0
            debits = db.query(sqla_func.coalesce(sqla_func.sum(WalletTransaction.amount), 0)).filter(
                WalletTransaction.wallet_id == wallet.id,
                WalletTransaction.type == "debit",
                WalletTransaction.status == "completed",
                WalletTransaction.created_at >= period_start,
                WalletTransaction.created_at < period_end
            ).scalar() or 0
            cash_in_val = float(credits)
            cash_out_val = float(abs(debits))
        cash_flow.append({
            "period": period_start.strftime("%b"),
            "cash_in": cash_in_val,
            "cash_out": cash_out_val
        })

    # 4. Risk Heatmap from Brain Engine risk runs
    risk_heatmap = []
    if BrainEngineRun:
        risk_runs = db.query(BrainEngineRun).filter(
            BrainEngineRun.tenant_id == tenant_id,
            BrainEngineRun.engine_type == "risk",
            BrainEngineRun.status == "success"
        ).order_by(BrainEngineRun.created_at.desc()).limit(10).all()
        for run in risk_runs:
            result = run.result_json or {}
            risk_heatmap.append({
                "country": result.get("country", "Unknown"),
                "category": result.get("primary_risk", "General"),
                "score": int(result.get("risk_score", 50))
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
