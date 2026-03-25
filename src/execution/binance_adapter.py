"""Binance live broker adapter (signed REST)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass
from urllib.error import HTTPError, URLError

from src.execution.models import FillEvent, OrderRequest, utc_now_iso


@dataclass
class BinanceConfig:
    base_url: str = "https://api.binance.com"
    recv_window_ms: int = 5000
    test_order: bool = True
    timeout_sec: int = 15
    max_retries: int = 3
    retry_backoff_sec: float = 0.5


class BinanceLiveAdapter:
    """Minimal Binance Spot signed-order adapter."""

    def __init__(self, config: BinanceConfig) -> None:
        self.config = config
        self.api_key = os.environ.get("EXCHANGE_API_KEY", "").strip()
        self.api_secret = os.environ.get("EXCHANGE_API_SECRET", "").strip()
        self._lot_step_cache: dict[str, float] = {}

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

    def _get_symbol_step_size(self, symbol: str) -> float:
        if symbol in self._lot_step_cache:
            return self._lot_step_cache[symbol]
        url = f"{self.config.base_url}/api/v3/exchangeInfo?symbol={symbol}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=self.config.timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
        step = 0.000001
        symbols = data.get("symbols", []) if isinstance(data, dict) else []
        if symbols:
            filters = symbols[0].get("filters", [])
            for fil in filters:
                if fil.get("filterType") == "LOT_SIZE":
                    try:
                        step = float(fil.get("stepSize", step))
                    except Exception:
                        pass
                    break
        self._lot_step_cache[symbol] = step
        return step

    @staticmethod
    def _normalize_qty(raw_qty: float, step_size: float) -> float:
        if step_size <= 0:
            return max(0.0, raw_qty)
        q = Decimal(str(max(0.0, raw_qty)))
        step = Decimal(str(step_size))
        units = (q / step).quantize(Decimal("1"), rounding=ROUND_DOWN)
        norm = (units * step).quantize(step, rounding=ROUND_DOWN)
        return float(norm)

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
                venue="binance_live",
                note="missing_exchange_credentials",
            )
        side = "BUY" if order.side == "buy" else "SELL"
        endpoint = "/api/v3/order/test" if self.config.test_order else "/api/v3/order"
        try:
            step_size = self._get_symbol_step_size(order.symbol)
        except Exception:
            step_size = 0.000001
        normalized_qty = self._normalize_qty(order.qty, step_size)
        if normalized_qty <= 0:
            return FillEvent(
                order_id=order.order_id,
                ts_utc=utc_now_iso(),
                symbol=order.symbol,
                side=order.side,
                qty=order.qty,
                fill_price=order.price_hint,
                status="rejected",
                venue="binance_live",
                note="normalized_qty_is_zero",
            )
        params = {
            "symbol": order.symbol,
            "side": side,
            "type": "MARKET",
            "quantity": f"{normalized_qty:.8f}",
            "newClientOrderId": order.order_id,
            "recvWindow": str(self.config.recv_window_ms),
            "timestamp": str(int(time.time() * 1000)),
        }
        for attempt in range(1, self.config.max_retries + 1):
            try:
                data = self._post(endpoint, params)
                if self.config.test_order:
                    return FillEvent(
                        order_id=order.order_id,
                        ts_utc=utc_now_iso(),
                        symbol=order.symbol,
                        side=order.side,
                        qty=normalized_qty,
                        fill_price=order.price_hint,
                        status="filled",
                        venue="binance_test_order",
                        note="accepted_by_binance_test_endpoint",
                    )
                fill_price = order.price_hint
                fills = data.get("fills") if isinstance(data, dict) else None
                if fills and isinstance(fills, list):
                    try:
                        fill_price = float(fills[0].get("price", order.price_hint))
                    except Exception:
                        pass
                return FillEvent(
                    order_id=order.order_id,
                    ts_utc=utc_now_iso(),
                    symbol=order.symbol,
                    side=order.side,
                    qty=normalized_qty,
                    fill_price=fill_price,
                    status="filled",
                    venue="binance_live",
                    note="live_order_submitted",
                )
            except HTTPError as e:
                body = ""
                try:
                    body = e.read().decode("utf-8")
                except Exception:
                    pass
                if e.code in (429, 500, 502, 503, 504) and attempt < self.config.max_retries:
                    time.sleep(self.config.retry_backoff_sec * attempt)
                    continue
                return FillEvent(
                    order_id=order.order_id,
                    ts_utc=utc_now_iso(),
                    symbol=order.symbol,
                    side=order.side,
                    qty=normalized_qty,
                    fill_price=order.price_hint,
                    status="rejected",
                    venue="binance_live",
                    note=f"http_error:{e.code}:{body[:120]}",
                )
            except URLError:
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_backoff_sec * attempt)
                    continue
                return FillEvent(
                    order_id=order.order_id,
                    ts_utc=utc_now_iso(),
                    symbol=order.symbol,
                    side=order.side,
                    qty=normalized_qty,
                    fill_price=order.price_hint,
                    status="rejected",
                    venue="binance_live",
                    note="network_error_after_retries",
                )
            except Exception as e:
                return FillEvent(
                    order_id=order.order_id,
                    ts_utc=utc_now_iso(),
                    symbol=order.symbol,
                    side=order.side,
                    qty=normalized_qty,
                    fill_price=order.price_hint,
                    status="rejected",
                    venue="binance_live",
                    note=f"submit_error:{type(e).__name__}",
                )
        return FillEvent(
            order_id=order.order_id,
            ts_utc=utc_now_iso(),
            symbol=order.symbol,
            side=order.side,
            qty=normalized_qty,
            fill_price=order.price_hint,
            status="rejected",
            venue="binance_live",
            note="submit_exhausted_without_result",
        )
