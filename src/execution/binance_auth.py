"""Shared Binance Spot REST signing helpers (read-only and trading paths)."""

from __future__ import annotations

import hashlib
import hmac
import time
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class BinanceAuthConfig:
    base_url: str = "https://api.binance.com"
    recv_window_ms: int = 5000
    timeout_sec: int = 15


def sign_query(secret: str, params: dict[str, str]) -> str:
    q = urllib.parse.urlencode(params)
    sig = hmac.new(secret.encode("utf-8"), q.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{q}&signature={sig}"


def signed_get(
    path: str,
    api_key: str,
    api_secret: str,
    config: BinanceAuthConfig | None = None,
) -> tuple[int, Any]:
    """GET signed endpoint; returns (http_status, parsed_json_or_error_dict)."""
    cfg = config or BinanceAuthConfig()
    params = {
        "timestamp": str(int(time.time() * 1000)),
        "recvWindow": str(cfg.recv_window_ms),
    }
    query = sign_query(api_secret, params)
    url = f"{cfg.base_url}{path}?{query}"
    req = urllib.request.Request(url, method="GET", headers={"X-MBX-APIKEY": api_key})
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_sec) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        try:
            err = json.loads(body)
        except Exception:
            err = {"raw": body}
        return e.code, err
    except Exception as e:
        return 0, {"error": type(e).__name__, "message": str(e)[:200]}
