from .base import EmailProvider, EmailError
from .local_dev import LocalDevEmailProvider

# Factory function to get the appropriate email provider
def get_email_provider(provider_name: str) -> EmailProvider:
    """Get email provider instance based on configuration."""
    if provider_name == "local_dev":
        return LocalDevEmailProvider()
    elif provider_name == "smtp":
        # TODO: Implement SMTP provider
        raise NotImplementedError("SMTP provider not yet implemented")
    elif provider_name == "sendgrid":
        # TODO: Implement SendGrid provider
        raise NotImplementedError("SendGrid provider not yet implemented")
    else:
        raise ValueError(f"Unknown email provider: {provider_name}")
