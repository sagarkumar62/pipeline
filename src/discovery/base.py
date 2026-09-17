from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List


class BaseDiscoverySource(ABC):
    """Abstract base class for pluggable discovery sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the discovery source."""
        pass

    @abstractmethod
    async def discover(self, limit: int = 100) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously yields raw candidate tool records discovered from the source.
        """
        pass
