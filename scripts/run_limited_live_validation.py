"""Run limited live validation cycles and store report.

Uses EXECUTION_MODE=live for adapter path validation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.main import run


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def main() -> int:
    cycles = int(os.environ.get("LIVE_VALIDATION_CYCLES", "24"))
    os.environ["EXECUTION_MODE"] = "live"
    live_fills_path = ROOT / "outputs" / "live_fills.jsonl"
    if live_fills_path.exists():
        live_fills_path.unlink()
    success = 0
    results = []
    for i in range(cycles):
        out_dir = ROOT / "outputs" / "live_validation" / f"cycle_{i:03d}"
        summary = run(str(out_dir))
        # limited validation pass condition: live mode path executed, no kill switch
        ok = (
            summary.get("execution_mode") == "live"
            and not summary.get("kill_switch", True)
            and summary.get("metrics", {}).get("mdd", 1.0) <= 0.15
        )
        if ok:
            success += 1
        results.append(
            {
                "cycle": i,
                "ok": ok,
                "execution_mode": summary.get("execution_mode"),
                "kill_switch": summary.get("kill_switch"),
                "mdd": summary.get("metrics", {}).get("mdd"),
                "n_fills": summary.get("n_fills"),
            }
        )

    pass_ratio = success / max(1, cycles)
    fills = _read_jsonl(live_fills_path)
    total_live_orders = len(fills)
    total_filled = sum(1 for r in fills if str(r.get("status", "")) == "filled")
    filled_ratio = total_filled / max(1, total_live_orders)
    credentials_present = bool(os.environ.get("EXCHANGE_API_KEY")) and bool(os.environ.get("EXCHANGE_API_SECRET"))
    passed = pass_ratio >= 0.95 and credentials_present and total_live_orders > 0 and filled_ratio >= 0.95
    report = {
        "passed": passed,
        "cycles": cycles,
        "success_cycles": success,
        "pass_ratio": pass_ratio,
        "credentials_present": credentials_present,
        "total_live_orders": total_live_orders,
        "total_filled": total_filled,
        "filled_ratio": filled_ratio,
        "results": results,
    }
    report_path = ROOT / "outputs" / "limited_live_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": passed,
                "pass_ratio": pass_ratio,
                "cycles": cycles,
                "credentials_present": credentials_present,
                "filled_ratio": filled_ratio,
                "total_live_orders": total_live_orders,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
