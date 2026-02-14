from .base import BillingProvider, BillingError
from .local_stub import LocalBillingStub

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
