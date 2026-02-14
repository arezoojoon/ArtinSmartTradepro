from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class BillingProvider(ABC):
    """Abstract base class for billing providers."""
    
    @abstractmethod
    async def create_customer(
        self, 
        tenant_id: uuid.UUID, 
        email: str, 
        name: Optional[str] = None
    ) -> str:
        """Create a customer and return provider customer ID."""
        pass
    
    @abstractmethod
    async def create_checkout_session(
        self, 
        customer_id: str, 
        plan: str, 
        success_url: str, 
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a checkout session and return session details."""
        pass
    
    @abstractmethod
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details."""
        pass
    
    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel subscription."""
        pass
    
    @abstractmethod
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle webhook event and return processed event data."""
        pass
    
    @abstractmethod
    def get_plan_price(self, plan: str) -> int:
        """Get plan price in cents."""
        pass
    
    @abstractmethod
    def get_plan_features(self, plan: str) -> Dict[str, Any]:
        """Get plan features."""
        pass


class BillingError(Exception):
    """Base exception for billing errors."""
    pass


class CustomerNotFoundError(BillingError):
    """Raised when customer is not found."""
    pass


class SubscriptionNotFoundError(BillingError):
    """Raised when subscription is not found."""
    pass


class WebhookSignatureError(BillingError):
    """Raised when webhook signature is invalid."""
    pass
