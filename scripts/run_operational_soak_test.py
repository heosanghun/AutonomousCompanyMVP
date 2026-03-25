"""Paper-mode soak test: many cycles, aggregate stability metrics (no live orders)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.main import run


def main() -> int:
    iterations = int(os.environ.get("SOAK_ITERATIONS", "60"))
    os.environ["EXECUTION_MODE"] = "paper"

    kill_any = False
    max_mdd = 0.0
    min_sharpe = 999.0
    failures = 0

    for i in range(iterations):
        out_dir = ROOT / "outputs" / "soak" / f"iter_{i:05d}"
        try:
            summary = run(str(out_dir))
        except Exception:
            failures += 1
            continue
        if summary.get("kill_switch"):
            kill_any = True
        m = summary.get("metrics") or {}
        max_mdd = max(max_mdd, float(m.get("mdd", 0.0)))
        s = float(m.get("sharpe", 0.0))
        min_sharpe = min(min_sharpe, s)

    if min_sharpe > 900:
        min_sharpe = 0.0

    passed = (
        not kill_any
        and failures == 0
        and max_mdd <= 0.2
        and min_sharpe >= -2.0
    )

    report = {
        "passed": passed,
        "iterations": iterations,
        "failures": failures,
        "kill_switch_any": kill_any,
        "max_mdd": max_mdd,
        "min_sharpe": min_sharpe,
    }
    out_path = ROOT / "outputs" / "soak_test_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
