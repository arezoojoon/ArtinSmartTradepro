"""
Hunter Phase 4 Provider Management API
Endpoints for managing enrichment providers
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services.hunter_provider_registry import registry, ProviderConfig, DisabledProviderError, NotConfiguredProviderError
from ..core.auth import get_current_user, get_current_tenant
from ..models.user import User
from ..models.tenant import Tenant

router = APIRouter(prefix="/hunter/providers", tags=["hunter"])

@router.get("/")
def list_providers(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """List all enrichment providers and their status"""
    providers = registry.list_providers()
    
    return [
        {
            "name": provider.name,
            "enabled": provider.enabled,
            "description": provider.description,
            "config_keys": list(provider.config.keys())
        }
        for provider in providers
    ]

@router.get("/{provider_name}")
def get_provider_details(
    provider_name: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get details for a specific provider"""
    config = registry.get_provider_config(provider_name)
    if not config:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Hide sensitive values in config
    safe_config = {}
    for key, value in config.config.items():
        if 'key' in key.lower() or 'secret' in key.lower():
            safe_config[key] = "***" if value else ""
        else:
            safe_config[key] = value
    
    return {
        "name": config.name,
        "enabled": config.enabled,
        "description": config.description,
        "config": safe_config
    }

@router.post("/{provider_name}/enable")
def enable_provider(
    provider_name: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Enable a provider"""
    success = registry.enable_provider(provider_name)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"message": f"Provider '{provider_name}' enabled successfully"}

@router.post("/{provider_name}/disable")
def disable_provider(
    provider_name: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Disable a provider"""
    success = registry.disable_provider(provider_name)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"message": f"Provider '{provider_name}' disabled successfully"}

@router.post("/{provider_name}/test")
def test_provider(
    provider_name: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Test if a provider is properly configured and accessible"""
    try:
        provider = registry.get_provider(provider_name)
        if not provider:
            raise HTTPException(
                status_code=400, 
                detail=f"Provider '{provider_name}' not enabled or not configured"
            )
        
        # For now, just return success if provider loads
        # In a real implementation, you might make a test API call
        return {
            "status": "success",
            "message": f"Provider '{provider_name}' is properly configured",
            "provider_name": provider.get_name()
        }
        
    except NotConfiguredProviderError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' not configured: {str(e)}"
        )
    except DisabledProviderError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' is disabled: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Provider test failed: {str(e)}"
        )
