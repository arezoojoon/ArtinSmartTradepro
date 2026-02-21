from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models.billing import Wallet, WalletTransaction
from uuid import UUID
import functools

class BillingService:
    @staticmethod
    async def get_wallet(db: AsyncSession, tenant_id: UUID) -> Wallet:
        """
        Get wallet for tenant.
        CRITICAL: Does NOT auto-create. Wallet must exist from registration.
        """
        res = await db.execute(select(Wallet).where(Wallet.tenant_id == tenant_id))
        wallet = res.scalar_one_or_none()
        if not wallet:
            raise HTTPException(status_code=500, detail="Wallet missing for tenant. Contact support.")
        return wallet

    @staticmethod
    async def deduct_balance(db: AsyncSession, tenant_id: UUID, amount: float, description: str) -> WalletTransaction:
        """
        ATOMIC DEDUCTION (Revenue Guard)
        Locks the wallet row with FOR UPDATE, checks balance, deducts, logs transaction.
        Caller MUST own the transaction boundary (commit/rollback).
        """
        res = await db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_id).with_for_update()
        )
        wallet = res.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        if float(wallet.balance) < amount:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient balance. Required: {amount}, Available: {wallet.balance}"
            )

        wallet.balance = float(wallet.balance) - amount
        
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
    async def refund(db: AsyncSession, tenant_id: UUID, amount: float, description: str) -> WalletTransaction:
        """
        ATOMIC REFUND
        Credits the wallet back after a failed action.
        Uses row lock to prevent race conditions.
        """
        res = await db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_id).with_for_update()
        )
        wallet = res.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found for refund")

        wallet.balance = float(wallet.balance) + amount
        
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
    async def add_credits(db: AsyncSession, tenant_id: UUID, amount: float, description: str, reference_id: str = None) -> WalletTransaction:
        """
        Add credits to a tenant's wallet (e.g. after Stripe payment).
        """
        res = await db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_id).with_for_update()
        )
        wallet = res.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        wallet.balance = float(wallet.balance) + amount
        
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
            
            # Using execute for async db
            res = await db.execute(
                select(Wallet).where(Wallet.tenant_id == current_user.current_tenant_id)
            )
            wallet = res.scalar_one_or_none()
            
            if not wallet or float(wallet.balance) < cost:
                 raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient funds. This action costs {cost} credits."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
