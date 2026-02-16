from abc import ABC, abstractmethod
from typing import List, Optional, Any

class EmailService(ABC):
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        from_email: Optional[str] = None
    ) -> bool:
        """Send a single email."""
        pass

    @abstractmethod
    async def send_batch(
        self,
        emails: List[dict]
    ) -> dict:
        """Send a batch of emails."""
        pass
