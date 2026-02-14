from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send an email and return delivery details."""
        pass
    
    @abstractmethod
    async def send_template_email(
        self,
        to_email: str,
        template_name: str,
        template_data: Dict[str, Any],
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send an email using a template."""
        pass


class EmailError(Exception):
    """Base exception for email errors."""
    pass


class EmailDeliveryError(EmailError):
    """Raised when email delivery fails."""
    pass


class EmailTemplateNotFoundError(EmailError):
    """Raised when email template is not found."""
    pass
