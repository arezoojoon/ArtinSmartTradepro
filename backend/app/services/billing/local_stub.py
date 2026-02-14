import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .base import BillingProvider, BillingError, CustomerNotFoundError, SubscriptionNotFoundError


class LocalBillingStub(BillingProvider):
    """Local stub billing provider for development/testing."""
    
    def __init__(self):
        # In-memory storage for testing
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.checkout_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def create_customer(
        self, 
        tenant_id: uuid.UUID, 
        email: str, 
        name: Optional[str] = None
    ) -> str:
        """Create a mock customer."""
        customer_id = f"cus_local_{tenant_id.hex[:8]}"
        
        self.customers[customer_id] = {
            "id": customer_id,
            "tenant_id": str(tenant_id),
            "email": email,
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        return customer_id
    
    async def create_checkout_session(
        self, 
        customer_id: str, 
        plan: str, 
        success_url: str, 
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a mock checkout session."""
        if customer_id not in self.customers:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")
        
        session_id = f"cs_local_{uuid.uuid4().hex[:8]}"
        
        # Simulate different session behaviors based on plan
        if plan == "whitelabel":
            # For whitelabel, simulate immediate success (setup fee)
            status = "complete"
        else:
            # For other plans, simulate pending checkout
            status = "open"
        
        session = {
            "id": session_id,
            "customer_id": customer_id,
            "plan": plan,
            "status": status,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "url": f"http://localhost:3000/checkout/success?session_id={session_id}" if status == "complete" else f"http://localhost:3000/checkout?session_id={session_id}"
        }
        
        self.checkout_sessions[session_id] = session
        
        # If complete, create subscription immediately
        if status == "complete":
            await self._create_subscription_from_session(session_id)
        
        return session
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details."""
        if subscription_id not in self.subscriptions:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        
        return self.subscriptions[subscription_id]
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel subscription."""
        if subscription_id not in self.subscriptions:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        
        subscription = self.subscriptions[subscription_id]
        subscription["status"] = "canceled"
        subscription["canceled_at"] = datetime.utcnow().isoformat()
        subscription["cancel_at_period_end"] = True
        
        return subscription
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle mock webhook events."""
        try:
            event = json.loads(payload.decode())
        except json.JSONDecodeError:
            raise BillingError("Invalid webhook payload")
        
        # Mock webhook processing
        event_type = event.get("type", "checkout.session.completed")
        
        if event_type == "checkout.session.completed":
            session_id = event.get("data", {}).get("object", {}).get("id")
            if session_id and session_id in self.checkout_sessions:
                await self._create_subscription_from_session(session_id)
        
        return {
            "type": event_type,
            "processed": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_plan_price(self, plan: str) -> int:
        """Get plan price in cents."""
        prices = {
            "professional": 29900,  # $299.00
            "enterprise": 99900,    # $999.00
            "whitelabel": 299900,  # $2,999.00
        }
        return prices.get(plan, 29900)
    
    def get_plan_features(self, plan: str) -> Dict[str, Any]:
        """Get plan features."""
        features = {
            "professional": {
                "max_users": 5,
                "max_tenants": 1,
                "api_calls_per_month": 10000,
                "support": "email",
                "custom_branding": False,
                "white_label": False,
            },
            "enterprise": {
                "max_users": 50,
                "max_tenants": 10,
                "api_calls_per_month": 100000,
                "support": "priority",
                "custom_branding": True,
                "white_label": False,
            },
            "whitelabel": {
                "max_users": -1,  # unlimited
                "max_tenants": -1,  # unlimited
                "api_calls_per_month": -1,  # unlimited
                "support": "dedicated",
                "custom_branding": True,
                "white_label": True,
            },
        }
        return features.get(plan, features["professional"])
    
    async def _create_subscription_from_session(self, session_id: str):
        """Create subscription from completed checkout session."""
        session = self.checkout_sessions.get(session_id)
        if not session:
            return
        
        customer_id = session["customer_id"]
        plan = session["plan"]
        
        subscription_id = f"sub_local_{uuid.uuid4().hex[:8]}"
        
        # Calculate period end (1 month from now)
        current_period_end = datetime.utcnow() + timedelta(days=30)
        
        subscription = {
            "id": subscription_id,
            "customer_id": customer_id,
            "plan": plan,
            "status": "active",
            "current_period_start": datetime.utcnow().isoformat(),
            "current_period_end": current_period_end.isoformat(),
            "cancel_at_period_end": False,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": session.get("metadata", {}),
        }
        
        self.subscriptions[subscription_id] = subscription
        
        # Update session status
        session["subscription_id"] = subscription_id
        
        return subscription
    
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer details."""
        return self.customers.get(customer_id)
    
    def list_subscriptions(self, customer_id: str) -> list:
        """List all subscriptions for a customer."""
        return [
            sub for sub in self.subscriptions.values()
            if sub["customer_id"] == customer_id
        ]
