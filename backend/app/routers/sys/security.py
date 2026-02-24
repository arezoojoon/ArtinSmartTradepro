"""
/sys/security — Security & Compliance Operations
Phase 6 Enhancement - Key rotation, anomaly detection, and compliance monitoring
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phase6 import SystemAdmin
from app.services.sys_admin_auth import get_current_sys_admin, write_sys_audit
from app.services.security_ops import SecurityOps

router = APIRouter()


# Pydantic Models
class KeyRotationRequest(BaseModel):
    target_type: str  # "system_admin" or "tenant" or "all_tenants"
    target_id: Optional[str] = None  # Admin ID or Tenant ID (if target_type is specific)
    reason: Optional[str] = None


class KeyRotationResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class SecurityAnomaly(BaseModel):
    type: str
    severity: str
    ip_address: Optional[str]
    admin_id: Optional[str]
    admin_email: Optional[str]
    count: int
    time_window: str
    details: Dict[str, Any]
    recommendation: str


class SecurityReport(BaseModel):
    report_period: Dict[str, Any]
    security_metrics: Dict[str, Any]
    current_anomalies: Dict[str, Any]
    compliance_status: Dict[str, Any]
    security_score: float
    recommendations: List[str]


class ComplianceStatus(BaseModel):
    overall_compliant: bool
    key_rotation_compliant: bool
    audit_compliance: bool
    access_control_compliant: bool
    last_check: str


@router.post("/rotate-keys", response_model=KeyRotationResponse, summary="Rotate Security Keys")
def rotate_keys(
    request: KeyRotationRequest,
    background_tasks: BackgroundTasks,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> KeyRotationResponse:
    """
    Rotate security keys for system admins or tenants
    """
    security_ops = SecurityOps(db)
    
    try:
        if request.target_type == "system_admin":
            if not request.target_id:
                raise HTTPException(status_code=400, detail="target_id required for system_admin rotation")
            
            details = security_ops.rotate_system_admin_keys(request.target_id)
            
            # Log audit
            write_sys_audit(
                db=db,
                action="rotate_system_admin_keys",
                resource_type="security",
                resource_id=request.target_id,
                actor_sys_admin_id=admin.id,
                before_state={"action": "key_rotation_initiated"},
                after_state={"status": "rotation_pending", "reason": request.reason}
            )
            
            return KeyRotationResponse(
                success=True,
                message="System admin key rotation initiated",
                details=details
            )
            
        elif request.target_type == "tenant":
            if not request.target_id:
                raise HTTPException(status_code=400, detail="target_id required for tenant rotation")
            
            details = security_ops.rotate_api_keys(request.target_id)
            
            # Log audit
            write_sys_audit(
                db=db,
                action="rotate_tenant_api_keys",
                resource_type="security",
                resource_id=request.target_id,
                actor_sys_admin_id=admin.id,
                before_state={"action": "api_key_rotation_initiated"},
                after_state={"status": "rotation_completed", "reason": request.reason}
            )
            
            return KeyRotationResponse(
                success=True,
                message="Tenant API key rotation completed",
                details=details
            )
            
        elif request.target_type == "all_tenants":
            details = security_ops.rotate_api_keys()
            
            # Log audit
            write_sys_audit(
                db=db,
                action="rotate_all_tenant_api_keys",
                resource_type="security",
                actor_sys_admin_id=admin.id,
                before_state={"action": "bulk_api_key_rotation_initiated"},
                after_state={"status": "rotation_completed", "tenants_rotated": details["total_rotated"], "reason": request.reason}
            )
            
            return KeyRotationResponse(
                success=True,
                message="All tenant API keys rotated successfully",
                details=details
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid target_type: {request.target_type}")
            
    except Exception as e:
        # Log error
        write_sys_audit(
            db=db,
            action="rotate_keys_error",
            resource_type="security",
            actor_sys_admin_id=admin.id,
            metadata={"error": str(e), "target_type": request.target_type, "target_id": request.target_id}
        )
        
        raise HTTPException(status_code=500, detail=f"Key rotation failed: {str(e)}")


@router.get("/anomalies", response_model=List[SecurityAnomaly], summary="Get Security Anomalies")
def get_security_anomalies(
    hours: int = 24,
    severity: Optional[str] = None,  # Filter by severity: low, medium, high, critical
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[SecurityAnomaly]:
    """
    Get detected security anomalies
    """
    security_ops = SecurityOps(db)
    anomalies = security_ops.detect_anomalies(hours=hours)
    
    # Filter by severity if specified
    if severity:
        anomalies = [a for a in anomalies if a["severity"] == severity]
    
    # Convert to response models
    anomaly_responses = []
    for anomaly in anomalies:
        anomaly_responses.append(SecurityAnomaly(**anomaly))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_security_anomalies",
        resource_type="security",
        actor_sys_admin_id=admin.id,
        metadata={"hours": hours, "severity": severity, "anomalies_count": len(anomaly_responses)}
    )
    
    return anomaly_responses


@router.get("/report", response_model=SecurityReport, summary="Get Security Report")
def get_security_report(
    days: int = 30,  # Report period in days
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> SecurityReport:
    """
    Generate comprehensive security report
    """
    security_ops = SecurityOps(db)
    report = security_ops.get_security_report(days=days)
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_security_report",
        resource_type="security",
        actor_sys_admin_id=admin.id,
        metadata={"days": days, "security_score": report["security_score"]}
    )
    
    return SecurityReport(**report)


@router.get("/compliance", response_model=ComplianceStatus, summary="Get Compliance Status")
def get_compliance_status(
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> ComplianceStatus:
    """
    Get current compliance status
    """
    security_ops = SecurityOps(db)
    compliance = security_ops._check_compliance_status()
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_compliance_status",
        resource_type="security",
        actor_sys_admin_id=admin.id,
        metadata=compliance
    )
    
    return ComplianceStatus(**compliance)


@router.get("/audit-trail", summary="Get Security Audit Trail")
def get_security_audit_trail(
    hours: int = 24,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get security-related audit trail entries
    """
    from app.models.phase6 import SysAuditLog
    from sqlalchemy import and_, or_
    
    # Build query
    query = db.query(SysAuditLog).filter(
        or_(
            SysAuditLog.action.like("security_%"),
            SysAuditLog.action.like("login_%"),
            SysAuditLog.action.in_([
                "tenant_impersonation",
                "bulk_user_creation",
                "sensitive_data_export",
                "system_settings_change"
            ])
        )
    )
    
    # Apply time filter
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    query = query.filter(SysAuditLog.created_at >= start_time, SysAuditLog.created_at <= end_time)
    
    # Apply event type filter
    if event_type:
        query = query.filter(SysAuditLog.action == event_type)
    
    # Apply severity filter (from metadata)
    if severity:
        query = query.filter(SysAuditLog.extra["severity"].astext == severity)
    
    # Order and limit
    audit_logs = query.order_by(SysAuditLog.created_at.desc()).limit(limit).all()
    
    # Format response
    entries = []
    for log in audit_logs:
        entry = {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "actor_sys_admin_id": str(log.actor_sys_admin_id) if log.actor_sys_admin_id else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "metadata": log.extra,
            "created_at": log.created_at.isoformat()
        }
        entries.append(entry)
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_security_audit_trail",
        resource_type="security",
        actor_sys_admin_id=admin.id,
        metadata={"hours": hours, "event_type": event_type, "severity": severity, "entries_count": len(entries)}
    )
    
    return {
        "entries": entries,
        "total_count": len(entries),
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "hours": hours
        }
    }


@router.post("/block-ip", summary="Block IP Address")
def block_ip_address(
    ip_address: str,
    reason: Optional[str] = None,
    duration_hours: int = 24,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    """
    Block an IP address (placeholder for actual implementation)
    """
    # This would typically update a firewall rules database or API
    
    # Log audit
    write_sys_audit(
        db=db,
        action="block_ip_address",
        resource_type="security",
        actor_sys_admin_id=admin.id,
        metadata={
            "ip_address": ip_address,
            "reason": reason,
            "duration_hours": duration_hours,
            "blocked_until": (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat()
        }
    )
    
    return {
        "message": f"IP address {ip_address} blocked for {duration_hours} hours",
        "ip_address": ip_address,
        "blocked_until": (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat()
    }


@router.post("/unblock-ip", summary="Unblock IP Address")
def unblock_ip_address(
    ip_address: str,
    reason: Optional[str] = None,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    """
    Unblock an IP address (placeholder for actual implementation)
    """
    # This would typically update a firewall rules database or API
    
    # Log audit
    write_sys_audit(
        db=db,
        action="unblock_ip_address",
        resource_type="security",
        actor_sys_admin_id=admin.id,
        metadata={
            "ip_address": ip_address,
            "reason": reason,
            "unblocked_at": datetime.utcnow().isoformat()
        }
    )
    
    return {
        "message": f"IP address {ip_address} unblocked",
        "ip_address": ip_address,
        "unblocked_at": datetime.utcnow().isoformat()
    }


@router.get("/blocked-ips", summary="Get Blocked IP Addresses")
def get_blocked_ips(
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get list of currently blocked IP addresses (placeholder implementation)
    """
    # This would typically query a firewall rules database or API
    
    # Mock data for demonstration
    blocked_ips = [
        {
            "ip_address": "192.168.1.100",
            "blocked_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "blocked_until": (datetime.utcnow() + timedelta(hours=22)).isoformat(),
            "reason": "Brute force attack detected",
            "blocked_by": "system"
        }
    ]
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_blocked_ips",
        resource_type="security",
        actor_sys_admin_id=admin.id,
        metadata={"blocked_ips_count": len(blocked_ips)}
    )
    
    return {
        "blocked_ips": blocked_ips,
        "total_count": len(blocked_ips)
    }
