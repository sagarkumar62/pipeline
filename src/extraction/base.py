from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseExtractor(ABC):
    """Interface for extractors converting raw discovery output to intermediate dicts."""

    @abstractmethod
    def extract(self, raw_item: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        pass
