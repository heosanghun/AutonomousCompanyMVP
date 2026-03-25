"""Compare exchange account balances with local summary / fills (best-effort)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.bootstrap_env import load_dotenv_files
from src.execution.binance_emergency import get_account_snapshot

load_dotenv_files()


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch signed Binance account snapshot and write report.")
    parser.add_argument("--out", default="outputs/exchange_reconcile_report.json")
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    snap = get_account_snapshot()
    summary_path = Path("outputs/summary.json")
    local = {}
    if summary_path.exists():
        try:
            local = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            local = {}

    usdt_free = None
    if snap.get("ok") and isinstance(snap.get("account"), dict):
        for b in snap["account"].get("balances", []) or []:
            if isinstance(b, dict) and b.get("asset") == "USDT":
                try:
                    usdt_free = float(b.get("free", 0.0))
                except (TypeError, ValueError):
                    usdt_free = None
                break

    payload = {
        "ok": bool(snap.get("ok")),
        "exchange": snap,
        "usdt_free": usdt_free,
        "local_summary_keys": list(local.keys()) if isinstance(local, dict) else [],
        "note": "Extend with per-asset delta checks once internal ledger is wired.",
    }
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
