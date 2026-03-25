"""Verify practical production readiness for autonomous operation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.compliance import load_readiness_bundle, verify_compliance_docs


def main() -> int:
    report = {
        "compliance_docs": verify_compliance_docs(ROOT),
        "readiness_bundle": load_readiness_bundle(ROOT / "outputs" / "readiness_bundle.json"),
        "live_guard_flag_exists": (ROOT / "outputs" / "live_readiness_approved.flag").exists(),
    }

    ok = True
    errors = []
    if not report["compliance_docs"]["ok"]:
        ok = False
        errors.append("missing_compliance_docs")
    if not report["readiness_bundle"]["exists"]:
        ok = False
        errors.append("missing_readiness_bundle")
    else:
        data = report["readiness_bundle"]["data"]
        if not bool(data.get("live_trading_approved", False)):
            ok = False
            errors.append("live_not_approved_in_bundle")
    if not report["live_guard_flag_exists"]:
        ok = False
        errors.append("missing_live_guard_flag")

    output = {
        "ok": ok,
        "errors": errors,
        "details": report,
    }
    out_path = ROOT / "outputs" / "production_readiness_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
