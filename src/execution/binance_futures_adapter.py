"""Minimal Binance USDT-M Futures signed adapter (USD-M /fapi)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from src.execution.models import FillEvent, OrderRequest, utc_now_iso


@dataclass
class BinanceFuturesConfig:
    base_url: str = "https://fapi.binance.com"
    recv_window_ms: int = 5000
    test_order: bool = True
    timeout_sec: int = 15


class BinanceFuturesAdapter:
    """Minimal Futures adapter: MARKET test or live order on /fapi/v1."""

    def __init__(self, config: BinanceFuturesConfig) -> None:
        self.config = config
        self.api_key = os.environ.get("EXCHANGE_API_KEY", "").strip()
        self.api_secret = os.environ.get("EXCHANGE_API_SECRET", "").strip()

    def _signed_query(self, params: dict) -> str:
        q = urllib.parse.urlencode(params)
        sig = hmac.new(self.api_secret.encode("utf-8"), q.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{q}&signature={sig}"

    def _post(self, path: str, params: dict) -> dict:
        query = self._signed_query(params)
        req = urllib.request.Request(
            f"{self.config.base_url}{path}",
            data=query.encode("utf-8"),
            method="POST",
            headers={"X-MBX-APIKEY": self.api_key, "Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=self.config.timeout_sec) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")

    def submit(self, order: OrderRequest) -> FillEvent:
        if not self.api_key or not self.api_secret:
            return FillEvent(
                order_id=order.order_id,
                ts_utc=utc_now_iso(),
                symbol=order.symbol,
                side=order.side,
                qty=order.qty,
                fill_price=order.price_hint,
                status="rejected",
                venue="binance_futures",
                note="missing_exchange_credentials",
                decision_id=order.decision_id,
                strategy_id=order.strategy_id,
                model_version=order.model_version,
                feature_version=order.feature_version,
                policy_version=order.policy_version,
            )
        side = "BUY" if order.side == "buy" else "SELL"
        path = "/fapi/v1/order/test" if self.config.test_order else "/fapi/v1/order"
        params = {
            "symbol": order.symbol,
            "side": side,
            "type": "MARKET",
            "quantity": f"{order.qty:.8f}",
            "recvWindow": str(self.config.recv_window_ms),
            "timestamp": str(int(time.time() * 1000)),
        }
        try:
            _ = self._post(path, params)
            note = "futures_test_accepted" if self.config.test_order else "futures_live_submitted"
            return FillEvent(
                order_id=order.order_id,
                ts_utc=utc_now_iso(),
                symbol=order.symbol,
                side=order.side,
                qty=order.qty,
                fill_price=order.price_hint,
                status="filled",
                venue="binance_futures_test" if self.config.test_order else "binance_futures",
                note=note,
                decision_id=order.decision_id,
                strategy_id=order.strategy_id,
                model_version=order.model_version,
                feature_version=order.feature_version,
                policy_version=order.policy_version,
            )
        except Exception as e:
            return FillEvent(
                order_id=order.order_id,
                ts_utc=utc_now_iso(),
                symbol=order.symbol,
                side=order.side,
                qty=order.qty,
                fill_price=order.price_hint,
                status="rejected",
                venue="binance_futures",
                note=f"submit_error:{type(e).__name__}",
                decision_id=order.decision_id,
                strategy_id=order.strategy_id,
                model_version=order.model_version,
                feature_version=order.feature_version,
                policy_version=order.policy_version,
            )
