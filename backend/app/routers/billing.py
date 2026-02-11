"""
Billing Router — Wallet balance, transactions, and credit management.
This endpoint serves the frontend wallet/dashboard pages.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.billing import Wallet, WalletTransaction
from app.middleware.auth import get_current_active_user
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


@router.get("/wallet")
async def get_wallet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get wallet balance and recent transactions.
    Used by: /dashboard (stats), /wallet (full page).
    """
    wallet = db.execute(
        select(Wallet).where(Wallet.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()

    if not wallet:
        return {"balance": 0.0, "currency": "AED", "transactions": []}

    transactions = db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(desc(WalletTransaction.created_at))
        .limit(50)
    ).scalars().all()

    return {
        "balance": float(wallet.balance),
        "currency": getattr(wallet, "currency", "AED"),
        "transactions": [
            {
                "id": str(tx.id),
                "amount": float(tx.amount),
                "type": tx.type,
                "description": tx.description,
                "status": getattr(tx, "status", "completed"),
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ],
    }


@router.get("/transactions")
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tx_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List wallet transactions with pagination and optional type filter.
    Types: credit, debit
    """
    wallet = db.execute(
        select(Wallet).where(Wallet.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()

    if not wallet:
        return {"total": 0, "transactions": []}

    query = select(WalletTransaction).where(
        WalletTransaction.wallet_id == wallet.id
    )
    if tx_type:
        query = query.where(WalletTransaction.type == tx_type)

    # Count
    from sqlalchemy import func
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total = db.execute(count_query).scalar() or 0

    # Fetch
    transactions = db.execute(
        query.order_by(desc(WalletTransaction.created_at))
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return {
        "total": total,
        "transactions": [
            {
                "id": str(tx.id),
                "amount": float(tx.amount),
                "type": tx.type,
                "description": tx.description,
                "status": getattr(tx, "status", "completed"),
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ],
    }
