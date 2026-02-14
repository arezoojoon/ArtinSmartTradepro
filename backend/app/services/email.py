from abc import ABC, abstractmethod
from typing import Optional
import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.billing import Invoice
# In a real app we might also store "outbox" emails in DB

class EmailProvider(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, body: str):
        pass

class LocalDevEmailProvider(EmailProvider):
    def send_email(self, to_email: str, subject: str, body: str):
        # Log to console
        print(f"--- [EMAIL SENT] ---\nTo: {to_email}\nSubject: {subject}\nBody:\n{body}\n--------------------")
        
        # Optionally retry storing in DB if we had an Outbox model, but console is fine for Phase 1 dev.

class SmtpEmailProvider(EmailProvider):
    def send_email(self, to_email: str, subject: str, body: str):
        # Stub for future implementation
        print(f"[SMTP STUB] Sending to {to_email}")

def get_email_provider() -> EmailProvider:
    # Read from settings in future
    return LocalDevEmailProvider()
