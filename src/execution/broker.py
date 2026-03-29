"""Broker abstraction with paper/live split."""

from __future__ import annotations

import json
import os
import random
from abc import ABC, abstractmethod
from dataclasses import replace
from pathlib import Path

from src.execution.binance_adapter import BinanceConfig, BinanceLiveAdapter
from src.execution.models import FillEvent, OrderRequest, utc_now_iso


class Broker(ABC):
    @abstractmethod
    def submit(self, order: OrderRequest) -> FillEvent:
        raise NotImplementedError


class PaperBroker(Broker):
    """Simple paper broker with configurable pseudo slippage."""

    def __init__(self, fills_path: str | Path, slippage_bps: float = 2.0, market_impact_factor: float = 0.5, run_id: str = "") -> None:
        self.fills_path = Path(fills_path)
        self.slippage_bps = slippage_bps
        self.market_impact_factor = market_impact_factor
        self.run_id = run_id
        self.fills_path.parent.mkdir(parents=True, exist_ok=True)

    def submit(self, order: OrderRequest) -> FillEvent:
        # Market impact simulation: base slippage + impact depending on qty.
        # Assuming typical liquidity makes impact quadratic or linear to order size.
        impact_bps = self.market_impact_factor * (order.qty ** 1.5)
        total_slip_bps = self.slippage_bps + impact_bps
        
        slip = (total_slip_bps / 10000.0) * (1.0 + random.uniform(-0.2, 0.2))
        direction = 1.0 if order.side == "buy" else -1.0
        fill_price = max(0.0001, order.price_hint * (1.0 + direction * slip))
        fill = FillEvent(
            order_id=order.order_id,
            ts_utc=utc_now_iso(),
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            fill_price=fill_price,
            status="filled",
            venue="paper",
            note=f"paper_fill_with_{self.slippage_bps}bps_base_slippage",
            decision_id=order.decision_id,
            strategy_id=order.strategy_id,
            model_version=order.model_version,
            feature_version=order.feature_version,
            policy_version=order.policy_version,
            run_id=self.run_id,
        )
        with self.fills_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(fill.as_dict(), ensure_ascii=True) + "\n")
        return fill


class LiveBrokerStub(Broker):
    """Safety stub for live mode. Blocks unless explicitly implemented."""

    def submit(self, order: OrderRequest) -> FillEvent:
        return FillEvent(
            order_id=order.order_id,
            ts_utc=utc_now_iso(),
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            fill_price=order.price_hint,
            status="rejected",
            venue="live_stub",
            note="live_broker_not_implemented",
            decision_id=order.decision_id,
            strategy_id=order.strategy_id,
            model_version=order.model_version,
            feature_version=order.feature_version,
            policy_version=order.policy_version,
        )


class LiveBrokerEnvGuard(Broker):
    """Live-mode safety guard.

    This broker verifies environment and readiness conditions.
    It still blocks real order placement by design unless replaced with
    a concrete exchange adapter in controlled deployment.
    """

    def __init__(
        self,
        readiness_flag_path: str | Path,
        fills_path: str | Path = "outputs/live_fills.jsonl",
        test_order: bool = True,
        run_id: str = "",
    ) -> None:
        self.readiness_flag_path = Path(readiness_flag_path)
        self.fills_path = Path(fills_path)
        self.run_id = run_id
        self.fills_path.parent.mkdir(parents=True, exist_ok=True)
        self.adapter = BinanceLiveAdapter(BinanceConfig(test_order=test_order))

    def _write_fill(self, fill: FillEvent) -> None:
        rec = fill.as_dict()
        if self.run_id:
            rec["run_id"] = self.run_id
        with self.fills_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=True) + "\n")

    def _ready(self) -> tuple[bool, str]:
        api_key = os.environ.get("EXCHANGE_API_KEY", "").strip()
        api_secret = os.environ.get("EXCHANGE_API_SECRET", "").strip()
        if not api_key or not api_secret:
            return False, "missing_exchange_credentials"
        if not self.readiness_flag_path.exists():
            return False, "missing_live_readiness_flag"
        return True, "ready"

    def submit(self, order: OrderRequest) -> FillEvent:
        ready, reason = self._ready()
        if not ready:
            fill = FillEvent(
                order_id=order.order_id,
                ts_utc=utc_now_iso(),
                symbol=order.symbol,
                side=order.side,
                qty=order.qty,
                fill_price=order.price_hint,
                status="rejected",
                venue="live_guard",
                note=reason,
                decision_id=order.decision_id,
                strategy_id=order.strategy_id,
                model_version=order.model_version,
                feature_version=order.feature_version,
                policy_version=order.policy_version,
                run_id=self.run_id,
            )
            self._write_fill(fill)
            return fill
        fill = replace(self.adapter.submit(order), run_id=self.run_id)
        self._write_fill(fill)
        return fill
