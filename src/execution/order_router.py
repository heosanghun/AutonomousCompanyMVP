"""Order router with mode separation and risk-aware gating."""

from __future__ import annotations

import itertools
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Optional

from src.execution.broker import Broker
from src.execution.models import FillEvent, OrderRequest, utc_now_iso


@dataclass
class RouterConfig:
    mode: str = "paper"  # paper/live
    symbol: str = "BTCUSDT"
    default_qty: float = 1.0
    max_notional_usd_per_order: float = 0.0  # 0 = disabled
    max_open_notional_usd: float = 0.0  # 0 = disabled; session cumulative
    strategy_id: str = "mvp_strategy_v1"
    model_version: str = "system1_v1"
    feature_version: str = "features_v1"
    policy_version: str = "policy_v1"


class OrderRouter:
    def __init__(self, broker: Broker, config: RouterConfig) -> None:
        self.broker = broker
        self.config = config
        self._order_counter = itertools.count(1)
        self._position_qty: float = 0.0
        self.last_reject_reason: str = ""

    def _notional_ok(self, side: str, qty: float, price: float) -> bool:
        self.last_reject_reason = ""
        notional = abs(float(qty)) * abs(float(price))
        cap = float(self.config.max_notional_usd_per_order)
        if cap > 0 and notional > cap + 1e-9:
            self.last_reject_reason = "max_notional_usd_per_order"
            return False
        open_cap = float(self.config.max_open_notional_usd)
        if open_cap <= 0:
            return True
        dq = float(qty) if side == "buy" else -float(qty)
        next_pos = self._position_qty + dq
        next_open = abs(next_pos) * abs(float(price))
        if next_open > open_cap + 1e-9:
            self.last_reject_reason = "max_open_notional_usd"
            return False
        return True

    def submit_action(
        self,
        action: int,
        price_hint: float,
        decision_id: str,
        reason_code: str,
        risk_approved: bool,
        feature_row: list[float] | None = None,
    ) -> Optional[FillEvent]:
        # 0=sell,1=hold,2=buy
        if action == 1:
            return None
        side = "buy" if action == 2 else "sell"
        feature_payload = feature_row if feature_row is not None else [price_hint]
        snap = hashlib.sha256(json.dumps(feature_payload, ensure_ascii=True).encode("utf-8")).hexdigest()
        order = OrderRequest(
            order_id=f"ord_{next(self._order_counter):08d}_{uuid.uuid4().hex[:8]}",
            ts_utc=utc_now_iso(),
            symbol=self.config.symbol,
            side=side,
            qty=self.config.default_qty,
            price_hint=float(price_hint),
            reason_code=reason_code,
            decision_id=decision_id,
            strategy_id=self.config.strategy_id,
            risk_approved=bool(risk_approved),
            model_version=self.config.model_version,
            feature_version=self.config.feature_version,
            policy_version=self.config.policy_version,
            input_snapshot_hash=snap,
        )
        if not order.risk_approved:
            return None
        if not self._notional_ok(order.side, order.qty, order.price_hint):
            return None
        fill = self.broker.submit(order)
        if fill is not None and getattr(fill, "status", "") == "filled":
            dq = float(fill.qty) if fill.side == "buy" else -float(fill.qty)
            self._position_qty += dq
        return fill
