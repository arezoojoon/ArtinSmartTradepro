"""
Campaign A/B Testing Router - Advanced Campaign Testing
Phase 6 Enhancement - Statistical analysis and optimization for email campaigns
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user
from app.services.campaign_ab import get_campaign_ab_service

router = APIRouter()


# Pydantic Models
class ABTestCreateRequest(BaseModel):
    campaign_name: str
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    test_duration_days: int = 14
    target_audience: Optional[Dict[str, Any]] = None


class ABTestCreateResponse(BaseModel):
    test_id: str
    status: str
    variants: List[Dict[str, Any]]
    test_duration_days: int
    start_date: str
    end_date: str


class ABTestStartRequest(BaseModel):
    test_id: str
    sample_size: Optional[int] = None


class ABTestStartResponse(BaseModel):
    test_id: str
    status: str
    sample_size: int
    start_date: str
    end_date: str


class CampaignEventRequest(BaseModel):
    test_id: str
    variant_id: str
    event_type: str
    contact_id: Optional[str] = None
    timestamp: Optional[str] = None


class CampaignEventResponse(BaseModel):
    test_id: str
    variant_id: str
    event_type: str
    recorded_at: str


class ABTestResultsResponse(BaseModel):
    test_id: str
    test_name: str
    status: str
    start_date: str
    end_date: str
    is_complete: bool
    sample_size: int
    primary_metric: str
    variant_metrics: Dict[str, Any]
    statistical_tests: List[Dict[str, Any]]
    winner: Optional[Dict[str, Any]]
    confidence_level: float


class ABTestStopResponse(BaseModel):
    test_id: str
    status: str
    stopped_at: str
    final_results: Dict[str, Any]


@router.post("/create", response_model=ABTestCreateResponse, summary="Create A/B Test")
async def create_ab_test(
    request: ABTestCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ABTestCreateResponse:
    """
    Create a new A/B test campaign
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get campaign A/B service
    campaign_service = get_campaign_ab_service(db)
    
    try:
        # Create A/B test
        result = await campaign_service.create_ab_test(
            campaign_name=request.campaign_name,
            tenant_id=str(tenant_id),
            variant_a=request.variant_a,
            variant_b=request.variant_b,
            test_duration_days=request.test_duration_days,
            target_audience=request.target_audience
        )
        
        return ABTestCreateResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A/B test creation failed: {str(e)}")


@router.post("/start", response_model=ABTestStartResponse, summary="Start A/B Test")
async def start_ab_test(
    request: ABTestStartRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ABTestStartResponse:
    """
    Start an A/B test campaign
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get campaign A/B service
    campaign_service = get_campaign_ab_service(db)
    
    try:
        # Start A/B test
        result = await campaign_service.start_ab_test(
            test_id=request.test_id,
            sample_size=request.sample_size
        )
        
        return ABTestStartResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A/B test start failed: {str(e)}")


@router.post("/record-event", response_model=CampaignEventResponse, summary="Record Campaign Event")
async def record_campaign_event(
    request: CampaignEventRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CampaignEventResponse:
    """
    Record a campaign event for A/B testing
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get campaign A/B service
    campaign_service = get_campaign_ab_service(db)
    
    try:
        # Parse timestamp if provided
        timestamp = None
        if request.timestamp:
            timestamp = datetime.fromisoformat(request.timestamp)
        
        # Record event
        result = await campaign_service.record_campaign_event(
            test_id=request.test_id,
            variant_id=request.variant_id,
            event_type=request.event_type,
            contact_id=request.contact_id,
            timestamp=timestamp
        )
        
        return CampaignEventResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event recording failed: {str(e)}")


@router.get("/results/{test_id}", response_model=ABTestResultsResponse, summary="Get A/B Test Results")
async def get_test_results(
    test_id: str,
    include_detailed_metrics: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ABTestResultsResponse:
    """
    Get A/B test results and statistical analysis
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get campaign A/B service
    campaign_service = get_campaign_ab_service(db)
    
    try:
        # Get test results
        result = await campaign_service.get_test_results(
            test_id=test_id,
            include_detailed_metrics=include_detailed_metrics
        )
        
        return ABTestResultsResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Results retrieval failed: {str(e)}")


@router.post("/stop/{test_id}", response_model=ABTestStopResponse, summary="Stop A/B Test")
async def stop_ab_test(
    test_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ABTestStopResponse:
    """
    Stop an A/B test and declare winner
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get campaign A/B service
    campaign_service = get_campaign_ab_service(db)
    
    try:
        # Stop test
        result = await campaign_service.stop_test(test_id)
        
        return ABTestStopResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test stop failed: {str(e)}")


@router.get("/recommendations/{test_id}", summary="Get Campaign Recommendations")
async def get_campaign_recommendations(
    test_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get recommendations based on A/B test results
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get campaign A/B service
    campaign_service = get_campaign_ab_service(db)
    
    try:
        # Get recommendations
        recommendations = await campaign_service.get_campaign_recommendations(test_id)
        
        return {
            "test_id": test_id,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


@router.get("/tests", summary="List A/B Tests")
async def list_ab_tests(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    List A/B tests
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get campaign A/B service
    campaign_service = get_campaign_ab_service(db)
    
    # No persistent A/B test table yet — return empty until implemented
    tests = []
    
    total = len(tests)
    paginated_tests = tests[offset:offset + limit]
    
    return {
        "tests": paginated_tests,
        "total_count": total,
        "limit": limit,
        "offset": offset,
        "status_filter": status
    }


@router.get("/metrics-summary", summary="Get Metrics Summary")
async def get_metrics_summary(
    test_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get summary of A/B testing metrics
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # No persistent A/B test table yet — return zeroed summary
    metrics_summary = {
        "total_tests": 0,
        "completed_tests": 0,
        "running_tests": 0,
        "created_tests": 0,
        "average_sample_size": 0,
        "average_test_duration_days": 0,
        "statistical_significance_rate": 0,
        "average_improvement": 0,
        "primary_metrics": {},
        "recent_performance": []
    }
    
    # If specific test requested, include its metrics
    if test_id:
        campaign_service = get_campaign_ab_service(db)
        try:
            test_results = await campaign_service.get_test_results(test_id)
            metrics_summary["specific_test"] = test_results
        except:
            metrics_summary["specific_test"] = {"error": "Test not found"}
    
    return metrics_summary


@router.get("/test-templates", summary="Get Test Templates")
async def get_test_templates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get A/B test templates
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    templates = [
        {
            "id": "subject_line_test",
            "name": "Subject Line Test",
            "description": "Test different email subject lines to improve open rates",
            "variant_a_template": {
                "subject": "Original Subject Line",
                "content": "Email content remains the same"
            },
            "variant_b_template": {
                "subject": "Test Subject Line",
                "content": "Email content remains the same"
            },
            "primary_metric": "open_rate",
            "recommended_duration": 7,
            "sample_size": 1000
        },
        {
            "id": "call_to_action_test",
            "name": "Call-to-Action Test",
            "description": "Test different CTA buttons and text to improve click rates",
            "variant_a_template": {
                "subject": "Email Subject",
                "content": "Email content with original CTA"
            },
            "variant_b_template": {
                "subject": "Email Subject",
                "content": "Email content with test CTA"
            },
            "primary_metric": "click_rate",
            "recommended_duration": 10,
            "sample_size": 1500
        },
        {
            "id": "sender_name_test",
            "name": "Sender Name Test",
            "description": "Test different sender names to improve engagement",
            "variant_a_template": {
                "subject": "Email Subject",
                "content": "Email content from original sender"
            },
            "variant_b_template": {
                "subject": "Email Subject",
                "content": "Email content from test sender"
            },
            "primary_metric": "open_rate",
            "recommended_duration": 7,
            "sample_size": 2000
        },
        {
            "id": "content_test",
            "name": "Content Test",
            "description": "Test different email content to improve conversions",
            "variant_a_template": {
                "subject": "Email Subject",
                "content": "Original email content"
            },
            "variant_b_template": {
                "subject": "Email Subject",
                "content": "Test email content"
            },
            "primary_metric": "conversion_rate",
            "recommended_duration": 14,
            "sample_size": 1000
        },
        {
            "id": "personalization_test",
            "name": "Personalization Test",
            "description": "Test personalization vs generic content",
            "variant_a_template": {
                "subject": "Email Subject",
                "content": "Generic email content"
            },
            "variant_b_template": {
                "subject": "Email Subject",
                "content": "Personalized email content"
            },
            "primary_metric": "conversion_rate",
            "recommended_duration": 14,
            "sample_size": 1500
        }
    ]
    
    return {
        "templates": templates,
        "total_count": len(templates),
        "categories": {
            "subject_line": [t for t in templates if t["id"] == "subject_line_test"],
            "call_to_action": [t for t in templates if t["id"] == "call_to_action_test"],
            "sender": [t for t in templates if t["id"] == "sender_name_test"],
            "content": [t for t in templates if t["id"] == "content_test"],
            "personalization": [t for t in templates if t["id"] == "personalization_test"]
        }
    }


@router.get("/statistical-info", summary="Get Statistical Information")
async def get_statistical_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get statistical information about A/B testing
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    statistical_info = {
        "significance_threshold": 0.05,
        "confidence_level": 0.95,
        "min_sample_size": 100,
        "test_methods": {
            "two_proportion_z_test": {
                "description": "Two-proportion z-test for comparing conversion rates",
                "use_case": "Comparing rates between two variants",
                "assumptions": [
                    "Independent samples",
                    "Large sample sizes (n > 30)",
                    "Normal distribution approximation"
                ]
            },
            "chi_square_test": {
                "description": "Chi-square test for categorical data",
                "use_case": "Testing categorical variables",
                "assumptions": [
                    "Expected frequency > 5",
                    "Independent observations",
                    "Random sampling"
                ]
            },
            "t_test": {
                "description": "Student's t-test for continuous data",
                "use_case": "Comparing means between variants",
                "assumptions": [
                    "Normal distribution",
                    "Equal variances (for pooled t-test)",
                    "Independent samples"
                ]
            }
        },
        "sample_size_calculation": {
            "description": "Sample size calculation for statistical power",
            "factors": [
                "Effect size (minimum detectable difference)",
                "Power (1 - β)",
                "Significance level (α)",
                "Population variance"
            ],
            "formula": "n = (Z_α/2 + Z_β)² * 2 * p * (1-p) / Δ²"
        },
        "confidence_intervals": {
            "description": "Confidence intervals for effect sizes",
            "interpretation": "Range of plausible values for the true effect",
            "calculation": "CI = point_estimate ± margin_of_error"
        }
    }
    
    return statistical_info
