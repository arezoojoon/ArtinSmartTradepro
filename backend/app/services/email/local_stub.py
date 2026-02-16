from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.email.base import EmailService
from app.models.email import EmailOutbox
from app.db.session import AsyncSessionLocal

class LocalStubEmailService(EmailService):
    """
    Stubs email sending by saving to a database table 'email_outbox'.
    Useful for development or when no SMTP is configured.
    """
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        from_email: Optional[str] = None
    ) -> bool:
        async with AsyncSessionLocal() as session:
            email = EmailOutbox(
                to_email=to_email,
                subject=subject,
                content=content,
                from_email=from_email or "system@artinsmarttrade.com",
                status="sent",  # Mark as sent for stub purposes
                provider="local_stub"
            )
            session.add(email)
            await session.commit()
            return True

    async def send_batch(self, emails: List[dict]) -> dict:
        results = {"success": 0, "failed": 0}
        async with AsyncSessionLocal() as session:
            for email_data in emails:
                email = EmailOutbox(
                    to_email=email_data["to_email"],
                    subject=email_data["subject"],
                    content=email_data["content"],
                    from_email=email_data.get("from_email", "system@artinsmarttrade.com"),
                    status="sent",
                    provider="local_stub"
                )
                session.add(email)
                results["success"] += 1
            await session.commit()
        return results
