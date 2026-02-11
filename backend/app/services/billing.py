from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.models.billing import Wallet, WalletTransaction
from uuid import UUID
import functools

class BillingService:
    @staticmethod
    def get_wallet(db: Session, tenant_id: UUID) -> Wallet:
        """
        Get wallet for tenant.
        CRITICAL: Does NOT auto-create. Wallet must exist from registration.
        """
        wallet = db.execute(select(Wallet).where(Wallet.tenant_id == tenant_id)).scalar_one_or_none()
        if not wallet:
            raise HTTPException(status_code=500, detail="Wallet missing for tenant. Contact support.")
        return wallet

    @staticmethod
    def deduct_balance(db: Session, tenant_id: UUID, amount: float, description: str) -> WalletTransaction:
        """
        ATOMIC DEDUCTION (Revenue Guard)
        Locks the wallet row with FOR UPDATE, checks balance, deducts, logs transaction.
        Caller MUST own the transaction boundary (commit/rollback).
        """
        wallet = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_id).with_for_update()
        ).scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        if wallet.balance < amount:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient balance. Required: {amount} {wallet.currency}, Available: {wallet.balance}"
            )

        wallet.balance -= amount
        
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=-amount,
            type="debit",
            description=description,
            status="completed"
        )
        db.add(transaction)
        return transaction

    @staticmethod
    def refund(db: Session, tenant_id: UUID, amount: float, description: str) -> WalletTransaction:
        """
        ATOMIC REFUND
        Credits the wallet back after a failed action.
        Uses row lock to prevent race conditions.
        """
        wallet = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_id).with_for_update()
        ).scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found for refund")

        wallet.balance += amount
        
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=amount,  # Positive for credit
            type="credit",
            description=description,
            status="completed"
        )
        db.add(transaction)
        return transaction

    @staticmethod
    def add_credits(db: Session, tenant_id: UUID, amount: float, description: str, reference_id: str = None) -> WalletTransaction:
        """
        Add credits to a tenant's wallet (e.g. after Stripe payment).
        """
        wallet = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_id).with_for_update()
        ).scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        wallet.balance += amount
        
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=amount,
            type="credit",
            description=description,
            reference_id=reference_id,
            status="completed"
        )
        db.add(transaction)
        return transaction


def precheck_balance(cost: float):
    """
    UX Guard Only.
    DO NOT RELY ON THIS FOR SECURITY.
    Real check happens in BillingService.deduct_balance with row locks.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if not db or not current_user:
                raise HTTPException(status_code=500, detail="Billing guard configuration error")
            
            wallet = db.execute(
                select(Wallet).where(Wallet.tenant_id == current_user.tenant_id)
            ).scalar_one_or_none()
            
            if not wallet or wallet.balance < cost:
                 raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient funds. This action costs {cost} credits."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
