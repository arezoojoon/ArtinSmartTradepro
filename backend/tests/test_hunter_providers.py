"""
Hunter Phase 4 Provider Tests
Test provider registry and management functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4
import os

from app.main import app
from app.services.hunter_provider_registry import ProviderRegistry, ProviderConfig, NotConfiguredProviderError
from app.services.hunter_enrichment import WebBasicProvider
from app.models.user import User
from app.models.tenant import Tenant

client = TestClient(app)

class TestProviderRegistry:
    """Test provider registry functionality"""
    
    def test_load_default_configs(self):
        """Test loading default provider configurations"""
        registry = ProviderRegistry()
        
        # Check that default configs are loaded
        assert "web_basic" in registry._configs
        assert "clearbit" in registry._configs
        assert "importyeti" in registry._configs
        
        # Check web_basic is enabled by default
        assert registry._configs["web_basic"].enabled is True
        
        # Check others are disabled by default
        assert registry._configs["clearbit"].enabled is False
        assert registry._configs["importyeti"].enabled is False
    
    def test_get_provider_enabled(self):
        """Test getting enabled provider"""
        registry = ProviderRegistry()
        
        with patch.dict(os.environ, {"HUNTER_PROVIDER_WEB_BASIC_ENABLED": "true"}):
            registry._load_default_configs()
            provider = registry.get_provider("web_basic")
            
            assert provider is not None
            assert isinstance(provider, WebBasicProvider)
            assert provider.get_name() == "web_basic"
    
    def test_get_provider_disabled(self):
        """Test getting disabled provider returns None"""
        registry = ProviderRegistry()
        
        with patch.dict(os.environ, {"HUNTER_PROVIDER_CLEARBIT_ENABLED": "false"}):
            registry._load_default_configs()
            provider = registry.get_provider("clearbit")
            
            assert provider is None
    
    def test_enable_disable_provider(self):
        """Test enabling and disabling providers"""
        registry = ProviderRegistry()
        
        # Disable web_basic
        success = registry.disable_provider("web_basic")
        assert success is True
        assert registry._configs["web_basic"].enabled is False
        
        # Try to get disabled provider
        provider = registry.get_provider("web_basic")
        assert provider is None
        
        # Re-enable web_basic
        success = registry.enable_provider("web_basic")
        assert success is True
        assert registry._configs["web_basic"].enabled is True
        
        # Should be able to get it now
        provider = registry.get_provider("web_basic")
        assert provider is not None
    
    def test_list_providers(self):
        """Test listing all providers"""
        registry = ProviderRegistry()
        providers = registry.list_providers()
        
        assert len(providers) >= 3  # web_basic, clearbit, importyeti
        
        provider_names = [p.name for p in providers]
        assert "web_basic" in provider_names
        assert "clearbit" in provider_names
        assert "importyeti" in provider_names
    
    def test_get_provider_config(self):
        """Test getting specific provider config"""
        registry = ProviderRegistry()
        
        config = registry.get_provider_config("web_basic")
        assert config is not None
        assert config.name == "web_basic"
        assert "timeout" in config.config
        assert "max_size" in config.config
        
        # Non-existent provider
        config = registry.get_provider_config("non_existent")
        assert config is None

class TestProviderAPI:
    """Test provider management API endpoints"""
    
    @pytest.fixture
    def test_tenant(self, db_session):
        """Create test tenant"""
        tenant = Tenant(
            id=uuid4(),
            name="Test Tenant",
            domain="test.example.com",
            settings={}
        )
        db_session.add(tenant)
        db_session.commit()
        return tenant
    
    @pytest.fixture
    def test_user(self, db_session, test_tenant):
        """Create test user"""
        user = User(
            id=uuid4(),
            email="test@example.com",
            current_tenant_id=test_tenant.id
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    def test_list_providers_api(self, test_user, test_tenant):
        """Test listing providers via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/hunter/providers/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        
        # Check web_basic provider
        web_basic = next((p for p in data if p["name"] == "web_basic"), None)
        assert web_basic is not None
        assert web_basic["enabled"] is True
        assert "description" in web_basic
        assert "config_keys" in web_basic
        
        app.dependency_overrides.clear()
    
    def test_get_provider_details_api(self, test_user, test_tenant):
        """Test getting provider details via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/hunter/providers/web_basic")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "web_basic"
        assert data["enabled"] is True
        assert "config" in data
        assert "timeout" in data["config"]
        
        # Sensitive keys should be masked
        app.dependency_overrides.clear()
    
    def test_enable_disable_provider_api(self, test_user, test_tenant):
        """Test enabling/disabling providers via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Disable web_basic
        response = client.post("/hunter/providers/web_basic/disable")
        assert response.status_code == 200
        assert "disabled successfully" in response.json()["message"]
        
        # Check it's disabled
        response = client.get("/hunter/providers/web_basic")
        data = response.json()
        assert data["enabled"] is False
        
        # Re-enable web_basic
        response = client.post("/hunter/providers/web_basic/enable")
        assert response.status_code == 200
        assert "enabled successfully" in response.json()["message"]
        
        # Check it's enabled
        response = client.get("/hunter/providers/web_basic")
        data = response.json()
        assert data["enabled"] is True
        
        app.dependency_overrides.clear()
    
    def test_test_provider_api_enabled(self, test_user, test_tenant):
        """Test testing an enabled provider"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.post("/hunter/providers/web_basic/test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "properly configured" in data["message"]
        assert data["provider_name"] == "web_basic"
        
        app.dependency_overrides.clear()
    
    def test_test_provider_api_disabled(self, test_user, test_tenant):
        """Test testing a disabled provider"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # clearbit should be disabled by default
        response = client.post("/hunter/providers/clearbit/test")
        assert response.status_code == 400
        assert "not enabled" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_test_provider_api_not_configured(self, test_user, test_tenant):
        """Test testing a provider that's enabled but not configured"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Enable clearbit but don't set API key
        response = client.post("/hunter/providers/clearbit/enable")
        assert response.status_code == 200
        
        response = client.post("/hunter/providers/clearbit/test")
        assert response.status_code == 400
        assert "not configured" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_get_nonexistent_provider(self, test_user, test_tenant):
        """Test getting details for non-existent provider"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/hunter/providers/nonexistent")
        assert response.status_code == 404
        assert "Provider not found" in response.json()["detail"]
        
        app.dependency_overrides.clear()

class TestProviderConfig:
    """Test provider configuration from environment variables"""
    
    def test_env_var_config(self):
        """Test configuration from environment variables"""
        with patch.dict(os.environ, {
            "HUNTER_PROVIDER_WEB_BASIC_ENABLED": "false",
            "HUNTER_WEB_BASIC_TIMEOUT": "20",
            "HUNTER_WEB_BASIC_USER_AGENT": "CustomAgent/1.0"
        }):
            registry = ProviderRegistry()
            registry._load_default_configs()
            
            config = registry.get_provider_config("web_basic")
            assert config.enabled is False
            assert config.config["timeout"] == 20
            assert config.config["user_agent"] == "CustomAgent/1.0"
    
    def test_clearbit_config_with_api_key(self):
        """Test Clearbit configuration with API key"""
        with patch.dict(os.environ, {
            "HUNTER_PROVIDER_CLEARBIT_ENABLED": "true",
            "CLEARBIT_API_KEY": "test-key-12345"
        }):
            registry = ProviderRegistry()
            registry._load_default_configs()
            
            config = registry.get_provider_config("clearbit")
            assert config.enabled is True
            assert config.config["api_key"] == "test-key-12345"
