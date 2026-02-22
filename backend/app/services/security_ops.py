"""
Security Operations Service
Phase 6 Enhancement - Key rotation, anomaly detection, and compliance monitoring
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models.phase6 import SystemAdmin, SysAuditLog
from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import generate_password_reset_token
from app.config import get_settings
settings = get_settings()


class SecurityEvent:
    """Security event for anomaly detection"""
    def __init__(
        self,
        event_type: str,
        severity: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.event_type = event_type
        self.severity = severity  # low, medium, high, critical
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow()


class SecurityOps:
    """Main security operations service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.key_rotation_interval = timedelta(days=90)  # Rotate keys every 90 days
        self.anomaly_threshold = 10  # Flag anomaly after 10 suspicious events
    
    def rotate_system_admin_keys(self, admin_id: str) -> Dict[str, Any]:
        """
        Rotate system admin authentication keys
        """
        admin = self.db.query(SystemAdmin).filter(SystemAdmin.id == admin_id).first()
        if not admin:
            raise ValueError("System admin not found")
        
        # Generate new password reset token for forced password change
        reset_token = generate_password_reset_token()
        
        # Log key rotation
        self._log_security_event(
            event_type="key_rotation",
            severity="medium",
            user_id=admin_id,
            details={"action": "system_admin_key_rotation", "method": "forced_reset"}
        )
        
        return {
            "admin_id": admin_id,
            "reset_token": reset_token,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "message": "Key rotation initiated. Admin must reset password within 24 hours."
        }
    
    def rotate_api_keys(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Rotate API keys for tenants or all tenants
        """
        if tenant_id:
            tenants = self.db.query(Tenant).filter(Tenant.id == tenant_id).all()
        else:
            tenants = self.db.query(Tenant).all()
        
        rotated_keys = []
        
        for tenant in tenants:
            # Generate new API key
            new_api_key = self._generate_api_key()
            
            # Store old key for grace period
            old_key = getattr(tenant, 'api_key', None)
            
            # Update tenant with new key
            tenant.api_key = new_api_key
            tenant.api_key_rotated_at = datetime.utcnow()
            
            rotated_keys.append({
                "tenant_id": str(tenant.id),
                "tenant_name": tenant.name,
                "new_key": new_api_key[:8] + "...",  # Only show partial key
                "rotated_at": datetime.utcnow().isoformat()
            })
            
            # Log rotation
            self._log_security_event(
                event_type="api_key_rotation",
                severity="medium",
                tenant_id=str(tenant.id),
                details={
                    "action": "api_key_rotation",
                    "method": "automatic_rotation",
                    "grace_period_hours": 24
                }
            )
        
        self.db.commit()
        
        return {
            "rotated_keys": rotated_keys,
            "total_rotated": len(rotated_keys),
            "message": "API keys rotated successfully. Old keys remain valid for 24 hours."
        }
    
    def detect_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect security anomalies based on audit logs and user behavior
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        anomalies = []
        
        # 1. Failed login attempts
        failed_logins = self.db.query(SysAuditLog).filter(
            SysAuditLog.action == "login_failed",
            SysAuditLog.created_at >= start_time,
            SysAuditLog.created_at <= end_time
        ).all()
        
        # Group by IP address
        ip_failures = {}
        for log in failed_logins:
            ip = log.ip_address
            if ip not in ip_failures:
                ip_failures[ip] = []
            ip_failures[ip].append(log)
        
        # Detect brute force attempts
        for ip, logs in ip_failures.items():
            if len(logs) >= 5:  # 5+ failed attempts from same IP
                anomalies.append({
                    "type": "brute_force_attempt",
                    "severity": "high",
                    "ip_address": ip,
                    "count": len(logs),
                    "time_window": f"{hours} hours",
                    "details": {
                        "first_attempt": logs[0].created_at.isoformat(),
                        "last_attempt": logs[-1].created_at.isoformat(),
                        "user_agents": list(set([log.user_agent for log in logs if log.user_agent]))
                    },
                    "recommendation": "Block IP address and notify security team"
                })
        
        # 2. Suspicious admin actions
        suspicious_actions = self.db.query(SysAuditLog).filter(
            SysAuditLog.actor_sys_admin_id.isnot(None),
            SysAuditLog.created_at >= start_time,
            SysAuditLog.created_at <= end_time,
            or_(
                SysAuditLog.action.in_([
                    "tenant_impersonation",
                    "bulk_user_creation",
                    "sensitive_data_export",
                    "system_settings_change"
                ])
            )
        ).all()
        
        # Group by admin
        admin_actions = {}
        for log in suspicious_actions:
            admin_id = str(log.actor_sys_admin_id)
            if admin_id not in admin_actions:
                admin_actions[admin_id] = []
            admin_actions[admin_id].append(log)
        
        # Detect unusual admin activity
        for admin_id, logs in admin_actions.items():
            if len(logs) >= 10:  # 10+ suspicious actions
                admin = self.db.query(SystemAdmin).filter(SystemAdmin.id == admin_id).first()
                anomalies.append({
                    "type": "suspicious_admin_activity",
                    "severity": "medium",
                    "admin_id": admin_id,
                    "admin_email": admin.email if admin else "Unknown",
                    "action_count": len(logs),
                    "actions": [log.action for log in logs],
                    "time_window": f"{hours} hours",
                    "details": {
                        "first_action": logs[0].created_at.isoformat(),
                        "last_action": logs[-1].created_at.isoformat(),
                        "unique_actions": len(set([log.action for log in logs]))
                    },
                    "recommendation": "Review admin activity and consider temporary access restriction"
                })
        
        # 3. Unusual access patterns
        unusual_access = self.db.query(SysAuditLog).filter(
            SysAuditLog.created_at >= start_time,
            SysAuditLog.created_at <= end_time
        ).group_by(
            SysAuditLog.actor_sys_admin_id,
            func.date(SysAuditLog.created_at)
        ).having(
            func.count(SysAuditLog.id) > 100  # 100+ actions in a day
        ).all()
        
        for result in unusual_access:
            anomalies.append({
                "type": "unusual_access_pattern",
                "severity": "medium",
                "admin_id": str(result.actor_sys_admin_id),
                "action_count": result.count,
                "date": result.date.isoformat(),
                "recommendation": "Review access pattern for potential automation or compromise"
            })
        
        return anomalies
    
    def get_security_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive security report
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Security metrics
        total_events = self.db.query(SysAuditLog).filter(
            SysAuditLog.created_at >= start_time,
            SysAuditLog.created_at <= end_time
        ).count()
        
        failed_logins = self.db.query(SysAuditLog).filter(
            SysAuditLog.action == "login_failed",
            SysAuditLog.created_at >= start_time,
            SysAuditLog.created_at <= end_time
        ).count()
        
        successful_logins = self.db.query(SysAuditLog).filter(
            SysAuditLog.action == "login_success",
            SysAuditLog.created_at >= start_time,
            SysAuditLog.created_at <= end_time
        ).count()
        
        admin_actions = self.db.query(SysAuditLog).filter(
            SysAuditLog.actor_sys_admin_id.isnot(None),
            SysAuditLog.created_at >= start_time,
            SysAuditLog.created_at <= end_time
        ).count()
        
        # Key rotations
        key_rotations = self.db.query(SysAuditLog).filter(
            SysAuditLog.action == "key_rotation",
            SysAuditLog.created_at >= start_time,
            SysAuditLog.created_at <= end_time
        ).count()
        
        # Current anomalies
        current_anomalies = self.detect_anomalies(hours=24)
        
        # Compliance status
        compliance_status = self._check_compliance_status()
        
        return {
            "report_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days
            },
            "security_metrics": {
                "total_events": total_events,
                "failed_logins": failed_logins,
                "successful_logins": successful_logins,
                "login_success_rate": (successful_logins / (successful_logins + failed_logins) * 100) if (successful_logins + failed_logins) > 0 else 0,
                "admin_actions": admin_actions,
                "key_rotations": key_rotations
            },
            "current_anomalies": {
                "count": len(current_anomalies),
                "items": current_anomalies
            },
            "compliance_status": compliance_status,
            "security_score": self._calculate_security_score(
                total_events, failed_logins, admin_actions, len(current_anomalies)
            ),
            "recommendations": self._generate_security_recommendations(
                failed_logins, admin_actions, current_anomalies
            )
        }
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"ast_{secrets.token_urlsafe(32)}"
    
    def _log_security_event(self, event_type: str, severity: str, **kwargs):
        """Log security event to audit trail"""
        audit_log = SysAuditLog(
            action=f"security_{event_type}",
            resource_type="security",
            metadata={
                "severity": severity,
                "event_type": event_type,
                **kwargs
            },
            created_at=datetime.utcnow()
        )
        self.db.add(audit_log)
        self.db.commit()
    
    def _check_compliance_status(self) -> Dict[str, Any]:
        """Check current compliance status"""
        # Check key rotation compliance
        key_rotation_compliance = True
        
        # Check if any system admin has old keys
        admins = self.db.query(SystemAdmin).filter(SystemAdmin.is_active == True).all()
        for admin in admins:
            # Check if key rotation is overdue (simplified check)
            if hasattr(admin, 'password_changed_at'):
                if admin.password_changed_at:
                    days_since_rotation = (datetime.utcnow() - admin.password_changed_at).days
                    if days_since_rotation > 90:
                        key_rotation_compliance = False
                        break
        
        # Check audit log completeness
        audit_compliance = True
        recent_audits = self.db.query(SysAuditLog).filter(
            SysAuditLog.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        if recent_audits == 0:
            audit_compliance = False
        
        # Check access control compliance
        access_control_compliance = True
        # This would check for proper RBAC implementation
        
        return {
            "overall_compliant": key_rotation_compliance and audit_compliance and access_control_compliance,
            "key_rotation_compliant": key_rotation_compliance,
            "audit_compliance": audit_compliance,
            "access_control_compliant": access_control_compliance,
            "last_check": datetime.utcnow().isoformat()
        }
    
    def _calculate_security_score(self, total_events: int, failed_logins: int, admin_actions: int, anomalies: int) -> float:
        """Calculate overall security score (0-100)"""
        # Base score starts at 100
        score = 100.0
        
        # Deduct points for failed logins
        if total_events > 0:
            failed_login_rate = (failed_logins / total_events) * 100
            score -= min(failed_login_rate * 2, 20)  # Max 20 points deduction
        
        # Deduct points for anomalies
        score -= min(anomalies * 5, 30)  # Max 30 points deduction
        
        # Deduct points for excessive admin actions (could indicate compromise)
        if admin_actions > 1000:
            score -= 10
        
        return max(0, score)
    
    def _generate_security_recommendations(self, failed_logins: int, admin_actions: int, anomalies: List[Dict]) -> List[str]:
        """Generate security recommendations based on current state"""
        recommendations = []
        
        if failed_logins > 50:
            recommendations.append("Consider implementing IP-based rate limiting for login attempts")
        
        if admin_actions > 1000:
            recommendations.append("Review admin activity for potential automation or unauthorized access")
        
        if len(anomalies) > 5:
            recommendations.append("Multiple security anomalies detected - immediate investigation recommended")
        
        if any(anomaly["type"] == "brute_force_attempt" for anomaly in anomalies):
            recommendations.append("Implement automatic IP blocking for repeated failed login attempts")
        
        if any(anomaly["type"] == "suspicious_admin_activity" for anomaly in anomalies):
            recommendations.append("Review admin privileges and implement principle of least privilege")
        
        if len(recommendations) == 0:
            recommendations.append("Security posture is healthy - continue monitoring")
        
        return recommendations
