import json
from typing import Dict, Any, Optional
from datetime import datetime
from .base import EmailProvider, EmailError, EmailDeliveryError


class LocalDevEmailProvider(EmailProvider):
    """Local development email provider that prints to console."""
    
    def __init__(self, store_emails: bool = True):
        self.store_emails = store_emails
        self.email_history: list = []
    
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
        """Send email by printing to console."""
        
        email_data = {
            "id": f"email_{datetime.utcnow().timestamp()}",
            "to_email": to_email,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
            "from_email": from_email or "noreply@artintrade.local",
            "reply_to": reply_to,
            "metadata": metadata or {},
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        
        # Print to console
        print("\n" + "="*80)
        print("📧 EMAIL SENT (Local Development)")
        print("="*80)
        print(f"To: {to_email}")
        print(f"From: {email_data['from_email']}")
        print(f"Subject: {subject}")
        if reply_to:
            print(f"Reply-To: {reply_to}")
        print("-"*80)
        if text_body:
            print("Text Body:")
            print(text_body)
        print("-"*80)
        print("HTML Body:")
        print(html_body)
        if metadata:
            print("-"*80)
            print("Metadata:")
            print(json.dumps(metadata, indent=2))
        print("="*80)
        print()
        
        # Store email history
        if self.store_emails:
            self.email_history.append(email_data)
        
        return {
            "message_id": email_data["id"],
            "status": "sent",
            "provider": "local_dev",
            "sent_at": email_data["sent_at"]
        }
    
    async def send_template_email(
        self,
        to_email: str,
        template_name: str,
        template_data: Dict[str, Any],
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email using a template."""
        
        # Simple template rendering
        templates = {
            "welcome": {
                "subject": "Welcome to Artin Smart Trade",
                "html": self._render_welcome_template(template_data),
                "text": self._render_welcome_text_template(template_data),
            },
            "password_reset": {
                "subject": "Reset your password",
                "html": self._render_password_reset_template(template_data),
                "text": self._render_password_reset_text_template(template_data),
            },
            "email_verification": {
                "subject": "Verify your email address",
                "html": self._render_email_verification_template(template_data),
                "text": self._render_email_verification_text_template(template_data),
            },
            "tenant_invitation": {
                "subject": "You're invited to join a workspace",
                "html": self._render_tenant_invitation_template(template_data),
                "text": self._render_tenant_invitation_text_template(template_data),
            },
        }
        
        if template_name not in templates:
            raise EmailError(f"Template '{template_name}' not found")
        
        template = templates[template_name]
        
        return await self.send_email(
            to_email=to_email,
            subject=subject or template["subject"],
            html_body=template["html"],
            text_body=template["text"],
            from_email=from_email,
            metadata={**template_data, "template_name": template_name}
        )
    
    def _render_welcome_template(self, data: Dict[str, Any]) -> str:
        """Render welcome email HTML template."""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e293b; color: white; padding: 20px; text-align: center;">
                <h1>Artin Smart Trade</h1>
                <p>AI Trade Operating System</p>
            </div>
            <div style="padding: 20px; background: #f8fafc;">
                <h2>Welcome, {data.get('full_name', 'User')}!</h2>
                <p>Thank you for signing up for Artin Smart Trade. We're excited to help you streamline your trading operations.</p>
                <p>Get started by:</p>
                <ul>
                    <li>Creating your first workspace</li>
                    <li>Inviting team members</li>
                    <li>Exploring our AI-powered features</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000/app" style="background: #f59e0b; color: #1e293b; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Get Started
                    </a>
                </div>
            </div>
            <div style="background: #1e293b; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <p>&copy; 2024 Artin Smart Trade. All rights reserved.</p>
            </div>
        </div>
        """
    
    def _render_welcome_text_template(self, data: Dict[str, Any]) -> str:
        """Render welcome email text template."""
        return f"""
        Welcome to Artin Smart Trade, {data.get('full_name', 'User')}!
        
        Thank you for signing up. We're excited to help you streamline your trading operations.
        
        Get started by:
        - Creating your first workspace
        - Inviting team members  
        - Exploring our AI-powered features
        
        Visit: http://localhost:3000/app
        
        Best regards,
        The Artin Smart Trade Team
        """
    
    def _render_password_reset_template(self, data: Dict[str, Any]) -> str:
        """Render password reset email HTML template."""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e293b; color: white; padding: 20px; text-align: center;">
                <h1>Artin Smart Trade</h1>
                <p>Password Reset</p>
            </div>
            <div style="padding: 20px; background: #f8fafc;">
                <h2>Reset Your Password</h2>
                <p>We received a request to reset your password. Click the button below to set a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000/auth/reset-password?token={data.get('token', '')}" style="background: #f59e0b; color: #1e293b; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                <p><strong>Important:</strong> This link will expire in 1 hour for security reasons.</p>
                <p>If you didn't request this password reset, you can safely ignore this email.</p>
            </div>
            <div style="background: #1e293b; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <p>&copy; 2024 Artin Smart Trade. All rights reserved.</p>
            </div>
        </div>
        """
    
    def _render_password_reset_text_template(self, data: Dict[str, Any]) -> str:
        """Render password reset email text template."""
        return f"""
        Reset Your Password
        
        We received a request to reset your password. Visit the link below to set a new password:
        
        http://localhost:3000/auth/reset-password?token={data.get('token', '')}
        
        Important: This link will expire in 1 hour for security reasons.
        
        If you didn't request this password reset, you can safely ignore this email.
        
        Best regards,
        The Artin Smart Trade Team
        """
    
    def _render_email_verification_template(self, data: Dict[str, Any]) -> str:
        """Render email verification HTML template."""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e293b; color: white; padding: 20px; text-align: center;">
                <h1>Artin Smart Trade</h1>
                <p>Email Verification</p>
            </div>
            <div style="padding: 20px; background: #f8fafc;">
                <h2>Verify Your Email Address</h2>
                <p>Thanks for signing up! Please verify your email address to complete your registration:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000/auth/verify-email?token={data.get('token', '')}" style="background: #f59e0b; color: #1e293b; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Verify Email
                    </a>
                </div>
                <p><strong>Important:</strong> This link will expire in 24 hours for security reasons.</p>
                <p>If you didn't create an account, you can safely ignore this email.</p>
            </div>
            <div style="background: #1e293b; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <p>&copy; 2024 Artin Smart Trade. All rights reserved.</p>
            </div>
        </div>
        """
    
    def _render_email_verification_text_template(self, data: Dict[str, Any]) -> str:
        """Render email verification text template."""
        return f"""
        Verify Your Email Address
        
        Thanks for signing up! Please verify your email address to complete your registration:
        
        http://localhost:3000/auth/verify-email?token={data.get('token', '')}
        
        Important: This link will expire in 24 hours for security reasons.
        
        If you didn't create an account, you can safely ignore this email.
        
        Best regards,
        The Artin Smart Trade Team
        """
    
    def _render_tenant_invitation_template(self, data: Dict[str, Any]) -> str:
        """Render tenant invitation HTML template."""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e293b; color: white; padding: 20px; text-align: center;">
                <h1>Artin Smart Trade</h1>
                <p>Workspace Invitation</p>
            </div>
            <div style="padding: 20px; background: #f8fafc;">
                <h2>You're Invited!</h2>
                <p>You've been invited to join <strong>{data.get('tenant_name', 'a workspace')}</strong> on Artin Smart Trade.</p>
                <p><strong>Role:</strong> {data.get('role', 'member').title()}</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000/auth/accept-invitation?token={data.get('token', '')}" style="background: #f59e0b; color: #1e293b; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Accept Invitation
                    </a>
                </div>
                <p><strong>Important:</strong> This invitation will expire in 7 days.</p>
                <p>If you don't have an account yet, you'll be able to create one when you accept the invitation.</p>
            </div>
            <div style="background: #1e293b; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <p>&copy; 2024 Artin Smart Trade. All rights reserved.</p>
            </div>
        </div>
        """
    
    def _render_tenant_invitation_text_template(self, data: Dict[str, Any]) -> str:
        """Render tenant invitation text template."""
        return f"""
        You're Invited!
        
        You've been invited to join {data.get('tenant_name', 'a workspace')} on Artin Smart Trade.
        
        Role: {data.get('role', 'member').title()}
        
        Accept your invitation: http://localhost:3000/auth/accept-invitation?token={data.get('token', '')}
        
        Important: This invitation will expire in 7 days.
        
        If you don't have an account yet, you'll be able to create one when you accept the invitation.
        
        Best regards,
        The Artin Smart Trade Team
        """
    
    def get_email_history(self) -> list:
        """Get all sent emails."""
        return self.email_history
    
    def clear_email_history(self):
        """Clear email history."""
        self.email_history.clear()
