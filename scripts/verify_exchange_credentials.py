"""Verify Binance API key/secret with a read-only signed call (no orders).

Loads env first, then secrets/exchange_credentials.json if keys missing.
Writes outputs/exchange_verify_report.json (no secrets in output).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bootstrap_env import load_dotenv_files
from src.execution.binance_auth import signed_get
from src.ops.secrets_loader import load_exchange_credentials_from_file


def main() -> int:
    os.chdir(ROOT)
    load_dotenv_files(ROOT)
    load_exchange_credentials_from_file(ROOT, overwrite=False)

    key = os.environ.get("EXCHANGE_API_KEY", "").strip()
    secret = os.environ.get("EXCHANGE_API_SECRET", "").strip()

    out_path = ROOT / "outputs" / "exchange_verify_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not key or not secret:
        report = {
            "ok": False,
            "reason": "missing_credentials",
            "hint": "Set EXCHANGE_API_KEY/SECRET in env or secrets/exchange_credentials.json",
        }
        out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 1

    status, body = signed_get("/api/v3/account", key, secret)
    ok = status == 200 and isinstance(body, dict) and "balances" in body
    report = {
        "ok": ok,
        "http_status": status,
        "can_trade": bool(body.get("canTrade")) if isinstance(body, dict) else None,
        "permissions": body.get("permissions") if isinstance(body, dict) else None,
        "error_code": body.get("code") if isinstance(body, dict) else None,
        "error_msg": (body.get("msg") or body.get("message"))[:200] if isinstance(body, dict) else None,
    }
    out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "permissions"}, ensure_ascii=True, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
