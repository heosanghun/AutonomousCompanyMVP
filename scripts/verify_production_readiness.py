"""Verify practical production readiness for autonomous operation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agentic.propose_agent import propose_next_actions
from src.ops.compliance import load_readiness_bundle, verify_compliance_docs


def main() -> int:
    profile = str(os.environ.get("FULL_OPS_PROFILE", "strict")).lower()
    report = {
        "compliance_docs": verify_compliance_docs(ROOT),
        "readiness_bundle": load_readiness_bundle(ROOT / "outputs" / "readiness_bundle.json"),
        "live_guard_flag_exists": (ROOT / "outputs" / "live_readiness_approved.flag").exists(),
        "human_live_approval": {"exists": (ROOT / "outputs" / "human_live_approval.json").exists(), "approved": False},
    }
    approval_path = ROOT / "outputs" / "human_live_approval.json"
    if approval_path.exists():
        try:
            approval_data = json.loads(approval_path.read_text(encoding="utf-8"))
            report["human_live_approval"]["approved"] = bool(approval_data.get("approved", False)) and bool(
                str(approval_data.get("approved_by", "")).strip()
            )
        except Exception:
            report["human_live_approval"]["approved"] = False

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
        if profile == "strict" and str(data.get("approved_by", "")).strip() in ("", "autonomous_system", "lab_auto_approved"):
            ok = False
            errors.append("invalid_bundle_approver_for_strict")
    if not report["live_guard_flag_exists"]:
        ok = False
        errors.append("missing_live_guard_flag")
    if profile == "strict" and not report["human_live_approval"]["approved"]:
        ok = False
        errors.append("missing_or_unapproved_human_live_approval")

    output = {
        "ok": ok,
        "profile": profile,
        "errors": errors,
        "details": report,
        "proposal_copilot": propose_next_actions({"errors": errors}),
    }
    out_path = ROOT / "outputs" / "production_readiness_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
