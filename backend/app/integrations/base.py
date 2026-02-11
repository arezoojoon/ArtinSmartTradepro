from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseIntegration(ABC):
    """
    Abstract Base Class for all External Data Integrations.
    Enforces a common interface for fetching and normalizing data.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch data from the external provider.
        kwargs should handle specific filters like 'commodity_code', 'country', 'date_range'.
        Should return a list of normalized dictionaries.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Confirms if the integration is reachable/active.
        """
        pass
