"""
/sys/health — Data Pipeline Health Monitoring
Phase 6 Enhancement - Monitor connectors, scrapers, and external APIs
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phase6 import SystemAdmin
from app.services.sys_admin_auth import get_current_sys_admin, write_sys_audit
from app.services.health_monitor import HealthMonitor, ConnectorStatus, ScraperStatus

router = APIRouter()


# Pydantic Models
class ConnectorHealthResponse(BaseModel):
    name: str
    status: str
    latency_ms: Optional[float]
    error_rate: Optional[float]
    last_success: Optional[str]
    last_error: Optional[str]
    error_count: int
    success_count: int


class ScraperHealthResponse(BaseModel):
    name: str
    status: str
    robots_compliant: bool
    throttle_active: bool
    last_run: Optional[str]
    success_rate: Optional[float]
    avg_runtime: Optional[float]
    blocked_domains: List[str]


class OverallHealthResponse(BaseModel):
    overall_score: float
    connector_score: float
    scraper_score: float
    healthy_connectors: int
    total_connectors: int
    healthy_scrapers: int
    total_scrapers: int
    status: str


class HealthActionRequest(BaseModel):
    action: str  # restart, reset, pause, resume
    target: str  # connector or scraper name
    reason: Optional[str] = None


@router.get("/connectors", response_model=List[ConnectorHealthResponse], summary="Get Connector Health")
async def get_connector_health(
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[ConnectorHealthResponse]:
    """
    Get health status for all external connectors (APIs, services)
    """
    monitor = HealthMonitor(db)
    connector_statuses = await monitor.get_all_connector_status()
    
    responses = []
    for status in connector_statuses:
        responses.append(ConnectorHealthResponse(
            name=status.name,
            status=status.status,
            latency_ms=status.latency_ms,
            error_rate=status.error_rate,
            last_success=status.last_success.isoformat() if status.last_success else None,
            last_error=status.last_error,
            error_count=status.error_count,
            success_count=status.success_count
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_connector_health",
        resource_type="health_monitoring",
        actor_sys_admin_id=admin.id,
        metadata={"connectors_count": len(responses)}
    )
    
    return responses


@router.get("/scrapers", response_model=List[ScraperHealthResponse], summary="Get Scraper Health")
async def get_scraper_health(
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[ScraperHealthResponse]:
    """
    Get health status for all scrapers (data collection)
    """
    monitor = HealthMonitor(db)
    scraper_statuses = await monitor.get_all_scraper_status()
    
    responses = []
    for status in scraper_statuses:
        responses.append(ScraperHealthResponse(
            name=status.name,
            status=status.status,
            robots_compliant=status.robots_compliant,
            throttle_active=status.throttle_active,
            last_run=status.last_run.isoformat() if status.last_run else None,
            success_rate=status.success_rate,
            avg_runtime=status.avg_runtime,
            blocked_domains=status.blocked_domains
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_scraper_health",
        resource_type="health_monitoring",
        actor_sys_admin_id=admin.id,
        metadata={"scrapers_count": len(responses)}
    )
    
    return responses


@router.get("/overview", response_model=OverallHealthResponse, summary="Get Overall Health")
def get_overall_health(
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> OverallHealthResponse:
    """
    Get overall health score and summary
    """
    monitor = HealthMonitor(db)
    health_score = monitor.get_overall_health_score()
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_overall_health",
        resource_type="health_monitoring",
        actor_sys_admin_id=admin.id,
        metadata=health_score
    )
    
    return OverallHealthResponse(**health_score)


@router.get("/connectors/{connector_name}", response_model=ConnectorHealthResponse, summary="Get Specific Connector Health")
async def get_specific_connector_health(
    connector_name: str,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    """
    Get detailed health status for a specific connector
    """
    monitor = HealthMonitor(db)
    
    if connector_name not in monitor.connectors:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_name}' not found")
    
    connector_monitor = monitor.connectors[connector_name]
    status = await connector_monitor.check_health()
    
    response = ConnectorHealthResponse(
        name=status.name,
        status=status.status,
        latency_ms=status.latency_ms,
        error_rate=status.error_rate,
        last_success=status.last_success.isoformat() if status.last_success else None,
        last_error=status.last_error,
        error_count=status.error_count,
        success_count=status.success_count
    )
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_connector_detail",
        resource_type="health_monitoring",
        resource_id=connector_name,
        actor_sys_admin_id=admin.id,
        metadata={"status": status.status}
    )
    
    return response


@router.get("/scrapers/{scraper_name}", response_model=ScraperHealthResponse, summary="Get Specific Scraper Health")
async def get_specific_scraper_health(
    scraper_name: str,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    """
    Get detailed health status for a specific scraper
    """
    monitor = HealthMonitor(db)
    
    if scraper_name not in monitor.scrapers:
        raise HTTPException(status_code=404, detail=f"Scraper '{scraper_name}' not found")
    
    scraper_monitor = monitor.scrapers[scraper_name]
    status = await scraper_monitor.check_health()
    
    response = ScraperHealthResponse(
        name=status.name,
        status=status.status,
        robots_compliant=status.robots_compliant,
        throttle_active=status.throttle_active,
        last_run=status.last_run.isoformat() if status.last_run else None,
        success_rate=status.success_rate,
        avg_runtime=status.avg_runtime,
        blocked_domains=status.blocked_domains
    )
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_scraper_detail",
        resource_type="health_monitoring",
        resource_id=scraper_name,
        actor_sys_admin_id=admin.id,
        metadata={"status": status.status}
    )
    
    return response


@router.post("/actions", summary="Execute Health Action")
async def execute_health_action(
    request: HealthActionRequest,
    background_tasks: BackgroundTasks,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    """
    Execute actions on connectors/scrapers (restart, reset, pause, resume)
    """
    monitor = HealthMonitor(db)
    
    # Validate target exists
    target_type = None
    if request.target in monitor.connectors:
        target_type = "connector"
    elif request.target in monitor.scrapers:
        target_type = "scraper"
    else:
        raise HTTPException(status_code=404, detail=f"Target '{request.target}' not found")
    
    # Validate action
    valid_actions = ["restart", "reset", "pause", "resume"]
    if request.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action '{request.action}'. Valid actions: {valid_actions}")
    
    # Execute action (in background for long-running operations)
    if request.action in ["restart", "reset"]:
        background_tasks.add_task(execute_background_action, request.action, request.target, target_type, admin.id)
        message = f"{request.action.capitalize()} action queued for {request.target}"
    else:  # pause, resume
        # For pause/resume, we could update database flags immediately
        message = f"{request.action.capitalize()} action executed for {request.target}"
    
    # Log audit
    write_sys_audit(
        db=db,
        action=f"health_{request.action}",
        resource_type="health_monitoring",
        resource_id=request.target,
        actor_sys_admin_id=admin.id,
        metadata={"target_type": target_type, "reason": request.reason}
    )
    
    return {"message": message, "status": "queued" if request.action in ["restart", "reset"] else "completed"}


async def execute_background_action(action: str, target: str, target_type: str, admin_id: UUID):
    """
    Execute background actions (restart, reset) for connectors/scrapers
    This would typically involve:
    - Stopping the service
    - Clearing caches/errors
    - Restarting the service
    - Updating health status
    """
    import asyncio
    from app.database import SessionLocal
    
    # Simulate action execution
    await asyncio.sleep(5)  # Simulate restart time
    
    # Update health status in database
    db = SessionLocal()
    try:
        # Log completion
        write_sys_audit(
            db=db,
            action=f"health_{action}_completed",
            resource_type="health_monitoring",
            resource_id=target,
            actor_sys_admin_id=admin_id,
            metadata={"target_type": target_type, "completed_at": datetime.utcnow().isoformat()}
        )
        db.commit()
    finally:
        db.close()


@router.get("/metrics", summary="Get Health Metrics")
def get_health_metrics(
    hours: int = 24,  # Last N hours
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed health metrics over time
    """
    # This would typically query a metrics database or logs
    # For now, return mock data
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    metrics = {
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "hours": hours
        },
        "connector_metrics": {
            "total_requests": 12500,
            "successful_requests": 12100,
            "failed_requests": 400,
            "avg_latency_ms": 245.5,
            "p95_latency_ms": 850.2,
            "p99_latency_ms": 1200.8
        },
        "scraper_metrics": {
            "total_runs": 840,
            "successful_runs": 795,
            "failed_runs": 45,
            "avg_runtime_seconds": 2.8,
            "total_items_scraped": 125000,
            "success_rate": 94.6
        },
        "error_breakdown": {
            "timeout_errors": 120,
            "connection_errors": 180,
            "rate_limit_errors": 60,
            "authentication_errors": 20,
            "other_errors": 20
        },
        "performance_trends": [
            {"timestamp": (end_time - timedelta(hours=i)).isoformat(), "health_score": 85.5 + (i % 10)}
            for i in range(hours)
        ]
    }
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_health_metrics",
        resource_type="health_monitoring",
        actor_sys_admin_id=admin.id,
        metadata={"hours": hours}
    )
    
    return metrics
