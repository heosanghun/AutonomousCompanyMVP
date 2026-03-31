"""Base interface for exchange adapters."""

from __future__ import annotations
import abc
from src.execution.models import FillEvent, OrderRequest

class BaseExchangeAdapter(abc.ABC):
    """Abstract base class for all exchange adapters."""

    @abc.abstractmethod
    def submit(self, order: OrderRequest) -> FillEvent:
        """Submits an order to the exchange and returns the fill event."""
        pass

    @abc.abstractmethod
    def fetch_balance(self, asset: str) -> float:
        """Fetches the available balance for a specific asset."""
        pass
