from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from houses.models import House


class BaseAnomalyDetector(ABC):
    domain: str = "generic"

    def __init__(self, house: House):
        self.house = house

    @abstractmethod
    def detect(self) -> List[Dict]:
        """Return normalized anomalies for this domain."""
        raise NotImplementedError

