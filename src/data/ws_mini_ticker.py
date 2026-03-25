"""Binance WebSocket miniTicker stream -> price series (optional websockets dependency)."""

from __future__ import annotations

import asyncio
import json
from typing import List


async def _collect_prices_async(
    symbol: str,
    n_samples: int,
    per_message_timeout_sec: float,
) -> List[float]:
    import websockets

    stream = f"{symbol.lower()}@miniTicker"
    uri = f"wss://stream.binance.com:9443/ws/{stream}"
    out: list[float] = []
    async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
        while len(out) < n_samples:
            raw = await asyncio.wait_for(ws.recv(), timeout=per_message_timeout_sec)
            msg = json.loads(raw)
            if isinstance(msg, dict) and "c" in msg:
                out.append(float(msg["c"]))
    return out


def fetch_binance_ws_mini_ticker_prices(
    symbol: str,
    n_samples: int,
    per_message_timeout_sec: float = 15.0,
) -> list[float]:
    try:
        import websockets  # noqa: F401
    except ImportError as e:
        raise RuntimeError("install_websockets: pip install -r requirements.txt") from e
    if n_samples < 2:
        raise ValueError("n_samples_must_be_at_least_2")
    return asyncio.run(_collect_prices_async(symbol, n_samples, per_message_timeout_sec))
