"""Emergency Binance Spot actions: cancel open orders (kill-switch support)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any
from urllib.error import HTTPError, URLError

from src.execution.binance_adapter import BinanceConfig


def _signed_query(secret: str, params: dict) -> str:
    q = urllib.parse.urlencode(params)
    sig = hmac.new(secret.encode("utf-8"), q.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{q}&signature={sig}"


def _delete_signed(path: str, params: dict, config: BinanceConfig) -> dict:
    api_key = os.environ.get("EXCHANGE_API_KEY", "").strip()
    api_secret = os.environ.get("EXCHANGE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        return {"ok": False, "error": "missing_exchange_credentials"}
    query = _signed_query(api_secret, params)
    url = f"{config.base_url}{path}?{query}"
    req = urllib.request.Request(url, method="DELETE", headers={"X-MBX-APIKEY": api_key})
    try:
        with urllib.request.urlopen(req, timeout=config.timeout_sec) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        return {"ok": False, "http_status": e.code, "error": body[:500]}
    except URLError as e:
        return {"ok": False, "error": str(e.reason)}


def cancel_all_open_orders(symbol: str | None = None, config: BinanceConfig | None = None) -> dict[str, Any]:
    """
    DELETE /api/v3/openOrders — Spot API requires symbol to cancel all open orders on that pair.
    """
    if not symbol:
        return {"ok": False, "error": "symbol_required_for_spot_cancel_all"}
    cfg = config or BinanceConfig()
    params: dict[str, str] = {
        "symbol": symbol,
        "recvWindow": str(cfg.recv_window_ms),
        "timestamp": str(int(time.time() * 1000)),
    }
    result = _delete_signed("/api/v3/openOrders", params, cfg)
    if isinstance(result, dict) and result.get("ok") is False:
        return result
    return {"ok": True, "response": result}


def get_account_snapshot(config: BinanceConfig | None = None) -> dict[str, Any]:
    """GET /api/v3/account — balances and permissions (signed)."""
    cfg = config or BinanceConfig()
    api_key = os.environ.get("EXCHANGE_API_KEY", "").strip()
    api_secret = os.environ.get("EXCHANGE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        return {"ok": False, "error": "missing_exchange_credentials"}
    params = {
        "recvWindow": str(cfg.recv_window_ms),
        "timestamp": str(int(time.time() * 1000)),
    }
    q = _signed_query(api_secret, params)
    url = f"{cfg.base_url}/api/v3/account?{q}"
    req = urllib.request.Request(url, method="GET", headers={"X-MBX-APIKEY": api_key})
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
        return {"ok": True, "account": data}
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        return {"ok": False, "http_status": e.code, "error": body[:500]}
    except URLError as e:
        return {"ok": False, "error": str(e.reason)}
