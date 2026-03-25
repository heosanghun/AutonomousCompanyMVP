"""Market data feed: mock (deterministic) or Binance public REST klines."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Tuple

import numpy as np


def generate_mock_data(n: int = 1000, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    ret = (rng.standard_normal(n) * 0.002 + 0.00035).astype(np.float32)
    vol = np.abs(rng.standard_normal(n) * 0.02).astype(np.float32)
    micro = (rng.standard_normal(n) * 0.5).astype(np.float32)
    ticks = np.column_stack([ret, vol, micro]).astype(np.float32)
    return ticks, ret


def fetch_binance_klines(
    symbol: str,
    interval: str = "1m",
    limit: int = 1000,
    base_url: str = "https://api.binance.com",
    timeout_sec: int = 20,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fetch recent klines from Binance public API and build tick/return arrays.

    Row layout matches mock: [return, vol_proxy, micro_proxy].
    """
    q = urllib.parse.urlencode({"symbol": symbol, "interval": interval, "limit": str(limit)})
    url = f"{base_url}/api/v3/klines?{q}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        raw = json.loads(resp.read().decode("utf-8") or "[]")
    if not isinstance(raw, list) or len(raw) < 3:
        raise RuntimeError("binance_klines_empty_or_invalid")

    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    for row in raw:
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            continue
        try:
            o = float(row[1])
            h = float(row[2])
            l = float(row[3])
            c = float(row[4])
        except (TypeError, ValueError):
            continue
        closes.append(c)
        highs.append(h)
        lows.append(l)

    n = len(closes)
    if n < 2:
        raise RuntimeError("binance_klines_too_short")

    arr = np.asarray(closes, dtype=np.float64)
    ret = np.diff(np.log(arr)).astype(np.float32)
    ret = np.concatenate([[0.0], ret]).astype(np.float32)
    hl = np.asarray(highs, dtype=np.float32) - np.asarray(lows, dtype=np.float32)
    vol_proxy = np.abs(ret) * 10.0 + np.maximum(hl / np.maximum(arr.astype(np.float32), 1e-12), 0.0)
    micro = (ret * 50.0).astype(np.float32)
    ticks = np.column_stack([ret, vol_proxy, micro]).astype(np.float32)
    return ticks, ret


def ws_prices_to_ticks_returns(prices: list[float]) -> tuple[np.ndarray, np.ndarray]:
    """Build tick/return arrays from a sequence of mid/last prices (e.g. WS miniTicker)."""
    arr = np.asarray(prices, dtype=np.float64)
    if arr.size < 2:
        raise RuntimeError("ws_prices_too_short")
    ret = np.diff(np.log(arr)).astype(np.float32)
    ret = np.concatenate([[0.0], ret]).astype(np.float32)
    vol_proxy = (np.abs(ret) * 10.0 + 0.001).astype(np.float32)
    micro = (ret * 50.0).astype(np.float32)
    ticks = np.column_stack([ret, vol_proxy, micro]).astype(np.float32)
    return ticks, ret
