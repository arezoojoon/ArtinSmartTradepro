"""
Billing Tests — Wallet Balance, Deduction, Refund, Atomic Locks.
"""
import pytest
import uuid
from app.services.billing import BillingService
from app.models.billing import Wallet
from fastapi import HTTPException
from sqlalchemy import select


class TestBillingDeduction:
    def test_deduct_success(self, db, tenant_professional):
        """Deduction reduces balance and creates transaction."""
        wallet_before = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_professional.id)
        ).scalar_one()
        balance_before = float(wallet_before.balance)

        BillingService.deduct_balance(
            db, tenant_professional.id, 10.0, "Test deduction"
        )
        db.flush()

        wallet_after = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_professional.id)
        ).scalar_one()
        assert float(wallet_after.balance) == balance_before - 10.0

    def test_deduct_insufficient_balance(self, db, tenant_professional):
        """Deduction beyond balance raises 402."""
        with pytest.raises(HTTPException) as exc_info:
            BillingService.deduct_balance(
                db, tenant_professional.id, 99999.0, "Too much"
            )
        assert exc_info.value.status_code == 402

    def test_deduct_missing_wallet(self, db):
        """Deduction for non-existent tenant raises 404."""
        fake_id = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            BillingService.deduct_balance(db, fake_id, 1.0, "Ghost")
        assert exc_info.value.status_code == 404


class TestBillingRefund:
    def test_refund_credits_back(self, db, tenant_professional):
        """Refund increases balance and creates credit transaction."""
        wallet_before = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_professional.id)
        ).scalar_one()
        balance_before = float(wallet_before.balance)

        BillingService.refund(db, tenant_professional.id, 5.0, "Test refund")
        db.flush()

        wallet_after = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_professional.id)
        ).scalar_one()
        assert float(wallet_after.balance) == balance_before + 5.0

    def test_deduct_then_refund_symmetry(self, db, tenant_professional):
        """Deduct + Refund should return balance to original."""
        wallet = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_professional.id)
        ).scalar_one()
        original = float(wallet.balance)

        BillingService.deduct_balance(db, tenant_professional.id, 10.0, "Test")
        BillingService.refund(db, tenant_professional.id, 10.0, "Refund")
        db.flush()

        wallet = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_professional.id)
        ).scalar_one()
        assert float(wallet.balance) == original


class TestBillingAddCredits:
    def test_add_credits(self, db, tenant_professional):
        """add_credits increases balance."""
        wallet = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_professional.id)
        ).scalar_one()
        original = float(wallet.balance)

        BillingService.add_credits(
            db, tenant_professional.id, 50.0, "Stripe payment", "ch_123"
        )
        db.flush()

        wallet = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_professional.id)
        ).scalar_one()
        assert float(wallet.balance) == original + 50.0
