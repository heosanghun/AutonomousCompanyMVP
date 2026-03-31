"""Real-time WebSocket tick streaming adapter.

Provides a continuous sub-millisecond data feed without relying on heavy
REST API polling, preparing the architecture for Kafka/Redis PubSub.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any

try:
    import websockets
except ImportError:
    websockets = None

logger = logging.getLogger(__name__)

class MarketStreamAdapter:
    """
    Subscribes to live market data (Binance WSS as default) and streams ticks.
    In a full distributed deployment, this module pushes to a local Redis PubSub or Kafka topic.
    """
    def __init__(self, symbol: str = "btcusdt", ws_url: str = "wss://stream.binance.com:9443/ws"):
        self.symbol = symbol.lower()
        self.ws_url = ws_url
        self.stream_name = f"{self.symbol}@miniTicker"
        
    async def connect_and_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator yielding real-time ticks.
        Fallback to mock data generation if websockets library is unavailable.
        """
        if websockets is None:
            logger.warning("websockets module not installed. Generating mock streaming data.")
            import random
            price = 50000.0
            while True:
                await asyncio.sleep(0.5)
                price += random.uniform(-10.0, 10.0)
                yield {
                    "e": "24hrMiniTicker",
                    "s": self.symbol.upper(),
                    "c": f"{price:.2f}",
                    "E": int(asyncio.get_event_loop().time() * 1000)
                }

        url = f"{self.ws_url}/{self.stream_name}"
        
        while True:
            try:
                async with websockets.connect(url) as ws:
                    logger.info(f"Connected to live WebSocket stream for {self.symbol}")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        yield data
            except Exception as e:
                logger.error(f"WebSocket connection dropped: {e}. Reconnecting in 3 seconds...")
                await asyncio.sleep(3.0)

    def process_tick(self, data: Dict[str, Any]) -> float:
        """Parses the raw JSON payload to extract current price."""
        try:
            return float(data.get("c", 0.0))
        except (ValueError, TypeError):
            return 0.0

    async def _test_runner(self):
        """Internal testing loop."""
        count = 0
        async for tick in self.connect_and_stream():
            price = self.process_tick(tick)
            print(f"[STREAM] {self.symbol.upper()}: {price}")
            count += 1
            if count >= 5:
                break
