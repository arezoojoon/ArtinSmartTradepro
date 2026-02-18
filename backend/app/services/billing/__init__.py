from .base import BillingProvider, BillingError
from .local_stub import LocalBillingStub

# Re-export BillingService from the legacy billing.py module
# This class is defined in app/services/billing.py (sibling file)
# but since this package shadows it, we need to import it explicitly.
import importlib, sys, os
_billing_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "billing.py")
if os.path.exists(_billing_file):
    _spec = importlib.util.spec_from_file_location("app.services._billing_legacy", _billing_file)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    BillingService = _mod.BillingService
    precheck_balance = _mod.precheck_balance

# Factory function to get the appropriate billing provider
def get_billing_provider(provider_name: str) -> BillingProvider:
    """Get billing provider instance based on configuration."""
    if provider_name == "local_stub":
        return LocalBillingStub()
    elif provider_name == "stripe":
        # TODO: Implement Stripe provider
        raise NotImplementedError("Stripe provider not yet implemented")
    else:
        raise ValueError(f"Unknown billing provider: {provider_name}")

