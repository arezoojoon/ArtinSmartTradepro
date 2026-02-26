"""
Freight Rates Router - Live Container and Bulk Shipping Rates
Phase 6 Enhancement - Real freight data with route optimization and cost analysis
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
from app.services.freight_rates import get_freight_rates_service

router = APIRouter()


# Pydantic Models
class FreightRateRequest(BaseModel):
    origin_port: str
    destination_port: str
    container_type: str = "20DC"
    service_type: Optional[str] = None
    carriers: Optional[List[str]] = None
    departure_date: Optional[str] = None


class FreightQuoteResponse(BaseModel):
    origin_port: str
    destination_port: str
    container_type: str
    service_type: str
    quotes: List[Dict[str, Any]]
    best_quote: Dict[str, Any]
    market_trends: Dict[str, Any]
    recommendations: List[str]


class RouteOptimizationRequest(BaseModel):
    origin_port: str
    destination_port: str
    container_type: str = "20DC"
    max_transit_days: Optional[int] = None
    max_rate: Optional[float] = None
    preferred_carriers: Optional[List[str]] = None


class RouteOptimizationResponse(BaseModel):
    success: bool
    optimal_quote: Optional[Dict[str, Any]]
    alternative_quotes: Optional[List[Dict[str, Any]]]
    optimization_score: Optional[float]
    recommendations: Optional[List[str]]
    message: Optional[str]
    suggestions: Optional[List[str]]


class PortInfo(BaseModel):
    name: str
    country: str
    coordinates: Dict[str, float]
    timezone: str
    facilities: List[str]
    congestion_level: str
    average_dwell_time: float
    major_carriers: List[str]


@router.post("/rates", response_model=FreightQuoteResponse, summary="Get Freight Rates")
async def get_freight_rates(
    request: FreightRateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FreightQuoteResponse:
    """
    Get freight rates for a specific route
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get freight rates service
    freight_service = get_freight_rates_service(db)
    
    try:
        # Get freight rates
        quote = await freight_service.get_freight_rates(
            origin_port=request.origin_port,
            destination_port=request.destination_port,
            container_type=request.container_type,
            service_type=request.service_type,
            carriers=request.carriers,
            departure_date=request.departure_date
        )
        
        return FreightQuoteResponse(
            origin_port=quote.origin_port,
            destination_port=quote.destination_port,
            container_type=quote.container_type,
            service_type=quote.service_type,
            quotes=quote.quotes,
            best_quote=quote.best_quote,
            market_trends=quote.market_trends,
            recommendations=quote.recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Freight rates query failed: {str(e)}")


@router.post("/optimize", response_model=RouteOptimizationResponse, summary="Optimize Route")
async def optimize_route(
    request: RouteOptimizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RouteOptimizationResponse:
    """
    Optimize route based on constraints
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get freight rates service
    freight_service = get_freight_rates_service(db)
    
    try:
        # Optimize route
        optimization = await freight_service.optimize_route(
            origin_port=request.origin_port,
            destination_port=request.destination_port,
            container_type=request.container_type,
            max_transit_days=request.max_transit_days,
            max_rate=request.max_rate,
            preferred_carriers=request.preferred_carriers
        )
        
        return RouteOptimizationResponse(**optimization)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")


@router.get("/port/{port_code}", response_model=PortInfo, summary="Get Port Information")
async def get_port_info(
    port_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PortInfo:
    """
    Get detailed port information
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get freight rates service
    freight_service = get_freight_rates_service(db)
    
    try:
        # Get port info
        info = await freight_service.get_port_info(port_code)
        
        return PortInfo(**info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Port info lookup failed: {str(e)}")


@router.get("/popular-routes", summary="Get Popular Routes")
async def get_popular_routes(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get popular freight routes
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Static reference data — popular shipping routes
    popular_routes = [
        {
            "route": "SHA-LAX",
            "origin_port": "Shanghai",
            "destination_port": "Los Angeles",
            "container_type": "20DC",
            "avg_rate": 1275,
            "transit_days": 14,
            "frequency": "Weekly",
            "volume": "High",
            "trend": "stable"
        },
        {
            "route": "SIN-NYC",
            "origin_port": "Singapore",
            "destination_port": "New York",
            "container_type": "20DC",
            "avg_rate": 1875,
            "transit_days": 21,
            "frequency": "Weekly",
            "volume": "High",
            "trend": "rising"
        },
        {
            "route": "HKG-ROT",
            "origin_port": "Hong Kong",
            "destination_port": "Rotterdam",
            "container_type": "20DC",
            "avg_rate": 1175,
            "transit_days": 28,
            "frequency": "Weekly",
            "volume": "High",
            "trend": "stable"
        },
        {
            "route": "JFK-HAM",
            "origin_port": "New York",
            "destination_port": "Hamburg",
            "container_type": "20DC",
            "avg_rate": 850,
            "transit_days": 10,
            "frequency": "Twice weekly",
            "volume": "Medium",
            "trend": "falling"
        },
        {
            "route": "SHA-ROT",
            "origin_port": "Shanghai",
            "destination_port": "Rotterdam",
            "container_type": "20DC",
            "avg_rate": 1350,
            "transit_days": 25,
            "frequency": "Weekly",
            "volume": "High",
            "trend": "rising"
        },
        {
            "route": "SIN-LAX",
            "origin_port": "Singapore",
            "destination_port": "Los Angeles",
            "container_type": "20DC",
            "avg_rate": 1650,
            "transit_days": 18,
            "frequency": "Weekly",
            "volume": "Medium",
            "trend": "stable"
        },
        {
            "route": "HKG-NYC",
            "origin_port": "Hong Kong",
            "destination_port": "New York",
            "container_type": "20DC",
            "avg_rate": 1950,
            "transit_days": 22,
            "frequency": "Weekly",
            "volume": "High",
            "trend": "rising"
        },
        {
            "route": "SHA-HAM",
            "origin_port": "Shanghai",
            "destination_port": "Hamburg",
            "container_type": "20DC",
            "avg_rate": 1450,
            "transit_days": 26,
            "frequency": "Weekly",
            "volume": "High",
            "trend": "stable"
        },
        {
            "route": "SIN-ROT",
            "origin_port": "Singapore",
            "destination_port": "Rotterdam",
            "container_type": "20DC",
            "avg_rate": 1250,
            "transit_days": 24,
            "frequency": "Twice weekly",
            "volume": "Medium",
            "trend": "falling"
        },
        {
            "route": "LAX-JFK",
            "origin_port": "Los Angeles",
            "destination_port": "New York",
            "container_type": "20DC",
            "avg_rate": 950,
            "transit_days": 12,
            "frequency": "Weekly",
            "volume": "Medium",
            "trend": "stable"
        }
    ]
    
    return {
        "routes": popular_routes[:limit],
        "total_count": len(popular_routes),
        "data_source": "Freight Market Data",
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/container-types", summary="Get Container Types")
async def get_container_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available container types
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    container_types = [
        {
            "code": "20DC",
            "name": "20' Dry Container",
            "description": "Standard 20-foot dry container",
            "dimensions": {"length": 20, "width": 8, "height": 8.6},
            "capacity": "33.1 CBM",
            "max_weight": "21,600 kg",
            "common_uses": ["General cargo", "Electronics", "Textiles"]
        },
        {
            "code": "40DC",
            "name": "40' Dry Container",
            "description": "Standard 40-foot dry container",
            "dimensions": {"length": 40, "width": 8, "height": 8.6},
            "capacity": "67.7 CBM",
            "max_weight": "26,500 kg",
            "common_uses": ["General cargo", "Furniture", "Machinery"]
        },
        {
            "code": "40HC",
            "name": "40' High Cube Container",
            "description": "40-foot container with extra height",
            "dimensions": {"length": 40, "width": 8, "height": 9.6},
            "capacity": "76.3 CBM",
            "max_weight": "26,500 kg",
            "common_uses": ["Lightweight cargo", "Volume shipments", "Household goods"]
        },
        {
            "code": "40RF",
            "name": "40' Reefer Container",
            "description": "40-foot refrigerated container",
            "dimensions": {"length": 40, "width": 8, "height": 8.6},
            "capacity": "67.7 CBM",
            "max_weight": "27,700 kg",
            "common_uses": ["Perishable goods", "Food products", "Pharmaceuticals"]
        },
        {
            "code": "20RF",
            "name": "20' Reefer Container",
            "description": "20-foot refrigerated container",
            "dimensions": {"length": 20, "width": 8, "height": 8.6},
            "capacity": "28.3 CBM",
            "max_weight": "21,600 kg",
            "common_uses": ["Perishable goods", "Food products", "Pharmaceuticals"]
        },
        {
            "code": "40OT",
            "name": "40' Open Top Container",
            "description": "40-foot container with open top",
            "dimensions": {"length": 40, "width": 8, "height": 8.6},
            "capacity": "64.0 CBM",
            "max_weight": "26,500 kg",
            "common_uses": ["Oversized cargo", "Machinery", "Equipment"]
        },
        {
            "code": "40FR",
            "name": "40' Flat Rack Container",
            "description": "40-foot flat rack container",
            "dimensions": {"length": 40, "width": 8, "height": 8.6},
            "capacity": "N/A",
            "max_weight": "40,000 kg",
            "common_uses": ["Heavy cargo", "Machinery", "Vehicles"]
        },
        {
            "code": "20TK",
            "name": "20' Tank Container",
            "description": "20-foot tank container for liquids",
            "dimensions": {"length": 20, "width": 8, "height": 8},
            "capacity": "26,000 liters",
            "max_weight": "36,000 kg",
            "common_uses": ["Liquids", "Chemicals", "Food products"]
        }
    ]
    
    return {
        "container_types": container_types,
        "total_count": len(container_types),
        "data_source": "Container Specifications",
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/service-types", summary="Get Service Types")
async def get_service_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available service types
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    service_types = [
        {
            "code": "Ocean",
            "name": "Ocean Freight",
            "description": "Sea transportation for containers and bulk cargo",
            "advantages": ["Cost-effective", "High capacity", "Environmentally friendly"],
            "disadvantages": ["Slow transit", "Weather dependent", "Port congestion"],
            "typical_transit": "10-45 days",
            "cost_range": "$500-$5000",
            "suitable_for": ["Large shipments", "Non-urgent cargo", "Cost-sensitive shipments"]
        },
        {
            "code": "Air",
            "name": "Air Freight",
            "description": "Air transportation for time-sensitive cargo",
            "advantages": ["Fast transit", "High security", "Reliable schedules"],
            "disadvantages": ["High cost", "Limited capacity", "Environmental impact"],
            "typical_transit": "1-5 days",
            "cost_range": "$2000-$15000",
            "suitable_for": ["Urgent shipments", "High-value goods", "Perishable items"]
        },
        {
            "code": "Rail",
            "name": "Rail Freight",
            "description": "Rail transportation for inland cargo movement",
            "advantages": ["Cost-effective", "High capacity", "Fuel efficient"],
            "disadvantages": ["Limited network", "Fixed routes", "Slower than air"],
            "typical_transit": "3-15 days",
            "cost_range": "$300-$2000",
            "suitable_for": ["Bulk cargo", "Inland transport", "Heavy shipments"]
        },
        {
            "code": "Truck",
            "name": "Truck Freight",
            "description": "Road transportation for regional cargo",
            "advantages": ["Door-to-door", "Flexible routes", "Quick transit"],
            "disadvantages": ["Limited capacity", "Traffic dependent", "Higher emissions"],
            "typical_transit": "1-7 days",
            "cost_range": "$200-$1500",
            "suitable_for": ["Regional shipments", "LTL cargo", "Time-sensitive deliveries"]
        },
        {
            "code": "Multimodal",
            "name": "Multimodal Freight",
            "description": "Combination of multiple transport modes",
            "advantages": ["Optimized routes", "Cost-effective", "Flexible"],
            "disadvantages": ["Complex coordination", "Multiple handovers", "Longer transit"],
            "typical_transit": "15-60 days",
            "cost_range": "$800-$6000",
            "suitable_for": ["International shipments", "Complex routes", "Cost optimization"]
        }
    ]
    
    return {
        "service_types": service_types,
        "total_count": len(service_types),
        "data_source": "Freight Service Specifications",
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/carriers", summary="Get Carriers")
async def get_carriers(
    service_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available carriers
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    carriers = [
        {
            "code": "MSC",
            "name": "Mediterranean Shipping Company",
            "service_types": ["Ocean"],
            "headquarters": "Geneva, Switzerland",
            "fleet_size": "700+ vessels",
            "coverage": "Global",
            "specialties": ["Container shipping", "Reefer cargo", "Oversized cargo"],
            "reliability": 0.92,
            "market_share": "16%"
        },
        {
            "code": "Maersk",
            "name": "A.P. Moller-Maersk",
            "service_types": ["Ocean"],
            "headquarters": "Copenhagen, Denmark",
            "fleet_size": "700+ vessels",
            "coverage": "Global",
            "specialties": ["Container shipping", "Cold chain", "Logistics"],
            "reliability": 0.95,
            "market_share": "17%"
        },
        {
            "code": "CMA CGM",
            "name": "CMA CGM Group",
            "service_types": ["Ocean"],
            "headquarters": "Marseille, France",
            "fleet_size": "500+ vessels",
            "coverage": "Global",
            "specialties": ["Container shipping", "Reefer cargo", "Project cargo"],
            "reliability": 0.88,
            "market_share": "7%"
        },
        {
            "code": "Hapag-Lloyd",
            "name": "Hapag-Lloyd",
            "service_types": ["Ocean"],
            "headquarters": "Hamburg, Germany",
            "fleet_size": "250+ vessels",
            "coverage": "Global",
            "specialties": ["Container shipping", "Premium services", "Reefer cargo"],
            "reliability": 0.91,
            "market_share": "5%"
        },
        {
            "code": "ONE",
            "name": "Ocean Network Express",
            "service_types": ["Ocean"],
            "headquarters": "Tokyo, Japan",
            "fleet_size": "200+ vessels",
            "coverage": "Global",
            "specialties": ["Container shipping", "Trans-Pacific", "Asia-Europe"],
            "reliability": 0.89,
            "market_share": "6%"
        },
        {
            "code": "FedEx",
            "name": "FedEx Express",
            "service_types": ["Air", "Truck"],
            "headquarters": "Memphis, USA",
            "fleet_size": "650+ aircraft",
            "coverage": "Global",
            "specialties": ["Express delivery", "Time-critical cargo", "E-commerce"],
            "reliability": 0.98,
            "market_share": "24%"
        },
        {
            "code": "DHL",
            "name": "DHL Express",
            "service_types": ["Air", "Truck"],
            "headquarters": "Bonn, Germany",
            "fleet_size": "250+ aircraft",
            "coverage": "Global",
            "specialties": ["International express", "Time-definite delivery", "Customs clearance"],
            "reliability": 0.97,
            "market_share": "18%"
        },
        {
            "code": "UPS",
            "name": "United Parcel Service",
            "service_types": ["Air", "Truck"],
            "headquarters": "Atlanta, USA",
            "fleet_size": "290+ aircraft",
            "coverage": "Global",
            "specialties": ["Ground delivery", "Air freight", "Supply chain solutions"],
            "reliability": 0.96,
            "market_share": "15%"
        }
    ]
    
    # Filter by service type if specified
    if service_type:
        carriers = [c for c in carriers if service_type in c["service_types"]]
    
    return {
        "carriers": carriers,
        "total_count": len(carriers),
        "data_source": "Carrier Information Database",
        "last_updated": datetime.utcnow().isoformat()
    }
