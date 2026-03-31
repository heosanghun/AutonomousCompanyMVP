"""Upbit live broker adapter placeholder."""

from __future__ import annotations

import os
import uuid
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass
from src.execution.models import FillEvent, OrderRequest, utc_now_iso
from src.execution.base_adapter import BaseExchangeAdapter

@dataclass
class UpbitConfig:
    base_url: str = "https://api.upbit.com"
    timeout_sec: int = 15

class UpbitLiveAdapter(BaseExchangeAdapter):
    """Upbit REST API adapter (Placeholder implementation)."""

    def __init__(self, config: UpbitConfig) -> None:
        self.config = config
        self.api_key = os.environ.get("UPBIT_API_KEY", "").strip()
        self.api_secret = os.environ.get("UPBIT_API_SECRET", "").strip()

    def _generate_jwt(self, query_string: str = "") -> str:
        # Placeholder for Upbit JWT signing logic
        # Typically uses PyJWT library, omitted here for dependency minimization
        return "mock_jwt_token"

    def fetch_balance(self, asset: str) -> float:
        """Fetches the free balance of the specified asset from Upbit."""
        if not self.api_key or not self.api_secret:
            return 0.0
            
        try:
            # Minimal mocked request
            return 0.0
        except Exception:
            return 0.0

    def submit(self, order: OrderRequest) -> FillEvent:
        """Submits an order to Upbit."""
        if not self.api_key or not self.api_secret:
            return FillEvent(
                order_id=order.order_id,
                ts_utc=utc_now_iso(),
                symbol=order.symbol,
                side=order.side,
                qty=order.qty,
                fill_price=order.price_hint,
                status="rejected",
                venue="upbit_live",
                note="missing_exchange_credentials",
                decision_id=order.decision_id,
                strategy_id=order.strategy_id,
                model_version=order.model_version,
                feature_version=order.feature_version,
                run_id=order.run_id
            )
            
        # Mock logic for upbit submission
        # In a real scenario, use `requests` and JWT headers to post to /v1/orders
        return FillEvent(
            order_id=order.order_id,
            ts_utc=utc_now_iso(),
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            fill_price=order.price_hint,
            status="filled",
            venue="upbit_live",
            note="upbit_mock_fill",
            decision_id=order.decision_id,
            strategy_id=order.strategy_id,
            model_version=order.model_version,
            feature_version=order.feature_version,
            run_id=order.run_id
        )
