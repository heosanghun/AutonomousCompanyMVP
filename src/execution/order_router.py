"""Order router with mode separation and risk-aware gating."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Optional

from src.execution.broker import Broker
from src.execution.models import FillEvent, OrderRequest, utc_now_iso


@dataclass
class RouterConfig:
    mode: str = "paper"  # paper/live
    symbol: str = "BTCUSDT"
    default_qty: float = 1.0
    strategy_id: str = "mvp_strategy_v1"


class OrderRouter:
    def __init__(self, broker: Broker, config: RouterConfig) -> None:
        self.broker = broker
        self.config = config
        self._order_counter = itertools.count(1)

    def submit_action(
        self,
        action: int,
        price_hint: float,
        decision_id: str,
        reason_code: str,
        risk_approved: bool,
    ) -> Optional[FillEvent]:
        # 0=sell,1=hold,2=buy
        if action == 1:
            return None
        side = "buy" if action == 2 else "sell"
        order = OrderRequest(
            order_id=f"ord_{next(self._order_counter):08d}",
            ts_utc=utc_now_iso(),
            symbol=self.config.symbol,
            side=side,
            qty=self.config.default_qty,
            price_hint=float(price_hint),
            reason_code=reason_code,
            decision_id=decision_id,
            strategy_id=self.config.strategy_id,
            risk_approved=bool(risk_approved),
        )
        if not order.risk_approved:
            return None
        return self.broker.submit(order)
