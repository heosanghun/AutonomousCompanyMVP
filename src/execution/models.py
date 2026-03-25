"""Execution domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass
class OrderRequest:
    order_id: str
    ts_utc: str
    symbol: str
    side: str
    qty: float
    price_hint: float
    reason_code: str
    decision_id: str
    strategy_id: str
    risk_approved: bool

    def as_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FillEvent:
    order_id: str
    ts_utc: str
    symbol: str
    side: str
    qty: float
    fill_price: float
    status: str  # filled/rejected
    venue: str
    note: str

    def as_dict(self) -> Dict:
        return asdict(self)
