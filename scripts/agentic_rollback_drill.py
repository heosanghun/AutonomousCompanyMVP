"""Rollback drill for agentic execution path."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.execution.binance_emergency import cancel_all_open_orders


def main() -> int:
    out = ROOT / "outputs" / "rollback_drill_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Drill actions: force paper mode + attempt cancel-all for record.
    os.environ["EXECUTION_MODE"] = "paper"
    os.environ["CANCEL_OPEN_ORDERS_ON_KILL_SWITCH"] = "1"
    symbol = str(os.environ.get("SYMBOL", "BTCUSDT"))
    cancel_result = cancel_all_open_orders(symbol=symbol)
    report = {
        "ok": True,
        "drill": "agentic_rollback",
        "actions": [
            "set EXECUTION_MODE=paper",
            "set CANCEL_OPEN_ORDERS_ON_KILL_SWITCH=1",
            f"attempt cancel open orders for {symbol}",
        ],
        "cancel_result": cancel_result,
    }
    out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

