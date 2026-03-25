"""End-to-end operational gate: compliance, production readiness, org sign-offs, exchange verify.

Environment overrides:
  FULL_OPS_SKIP_EXCHANGE_VERIFY=1  — do not call Binance (e.g. no keys yet)
  FULL_OPS_SKIP_ORG_SIGNOFFS=1     — skip organizational_signoffs.json
  FULL_OPS_ACCEPT_LAB_DEMO=1       — accept lab_demo_closure in organizational_signoffs.json
  FULL_OPS_ACCEPT_WAIVERS=1        — accept external dependency waivers file
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bootstrap_env import load_dotenv_files
from src.ops.compliance import (
    verify_compliance_docs,
    verify_extended_compliance_docs,
    verify_organizational_signoffs,
)
from src.ops.secrets_loader import load_exchange_credentials_from_file


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _load_waivers() -> dict:
    path = ROOT / "outputs" / "external_dependency_waivers.json"
    if not path.exists():
        return {"exists": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"exists": True, "ok": False, "reason": "invalid_json"}
    required = [
        "allow_missing_exchange_credentials",
        "allow_non_legal_completion",
        "allow_non_tax_completion",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        return {"exists": True, "ok": False, "reason": "missing_keys", "missing": missing}
    ok = all(bool(data.get(k, False)) for k in required)
    return {"exists": True, "ok": ok, "data": data}


def _has_exchange_creds() -> bool:
    load_dotenv_files(ROOT)
    load_exchange_credentials_from_file(ROOT, overwrite=False)
    return bool(
        os.environ.get("EXCHANGE_API_KEY", "").strip()
        and os.environ.get("EXCHANGE_API_SECRET", "").strip()
    )


def main() -> int:
    os.chdir(ROOT)

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_production_readiness.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    prod_path = ROOT / "outputs" / "production_readiness_report.json"
    prod_ok = False
    if prod_path.exists():
        prod_ok = bool(json.loads(prod_path.read_text(encoding="utf-8")).get("ok"))

    extended = verify_extended_compliance_docs(ROOT)
    org_path = ROOT / "outputs" / "organizational_signoffs.json"
    if _truthy("FULL_OPS_SKIP_ORG_SIGNOFFS"):
        org = {"ok": True, "skipped": True}
    else:
        org = verify_organizational_signoffs(org_path)

    if _truthy("FULL_OPS_SKIP_EXCHANGE_VERIFY"):
        exch = {"ok": True, "skipped": True}
    elif not _has_exchange_creds():
        exch = {"ok": False, "reason": "no_credentials", "hint": "Add secrets or set FULL_OPS_SKIP_EXCHANGE_VERIFY=1"}
    else:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_exchange_credentials.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        exch_path = ROOT / "outputs" / "exchange_verify_report.json"
        exch_detail = json.loads(exch_path.read_text(encoding="utf-8")) if exch_path.exists() else {}
        exch = {"ok": r.returncode == 0, "details": exch_detail}

    base_compliance = verify_compliance_docs(ROOT)
    waivers = _load_waivers()
    if _truthy("FULL_OPS_ACCEPT_WAIVERS") and waivers.get("ok", False):
        if exch.get("reason") == "no_credentials":
            exch = {"ok": True, "waived": True, "reason": "waived_missing_exchange_credentials"}

    overall = (
        prod_ok
        and base_compliance["ok"]
        and extended["ok"]
        and org["ok"]
        and exch["ok"]
    )

    report = {
        "ok": overall,
        "production_readiness": {"ok": prod_ok},
        "compliance_docs": base_compliance,
        "extended_compliance_docs": extended,
        "organizational_signoffs": org,
        "exchange_verification": exch,
        "external_dependency_waivers": waivers,
    }
    out = ROOT / "outputs" / "full_operational_gate_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps({"ok": overall, "path": str(out)}, ensure_ascii=True, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
