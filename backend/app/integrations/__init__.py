"""
Data Integration Base — Interface-first design.
All integration clients inherit from this base.
Swap implementations without changing consumers.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging
import datetime

logger = logging.getLogger(__name__)


class BaseIntegrationClient(ABC):
    """Base class for all external data providers."""

    provider_name: str = "base"
    is_mock: bool = True  # True until real API key is configured

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify connectivity to the provider."""
        raise NotImplementedError

    def log_request(self, method: str, params: dict, result: Any = None, error: str = None):
        """Structured logging for all API interactions."""
        log_entry = {
            "provider": self.provider_name,
            "method": method,
            "params": params,
            "is_mock": self.is_mock,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "error": error,
        }
        if error:
            logger.error(f"Integration error: {log_entry}")
        else:
            logger.info(f"Integration call: {log_entry}")
