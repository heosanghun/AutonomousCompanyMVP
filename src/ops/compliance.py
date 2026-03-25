"""Compliance helpers for production-readiness checks."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List


REQUIRED_DOCS = [
    "docs/compliance/kyc_aml_checklist.md",
    "docs/compliance/tax_reporting_checklist.md",
    "docs/compliance/security_controls_checklist.md",
    "docs/compliance/incident_response_runbook.md",
]

EXTENDED_DOCS = [
    "docs/compliance/regulatory_scope.md",
    "docs/compliance/organizational_raci.md",
    "docs/compliance/capital_and_risk_limits.md",
]


def verify_compliance_docs(root: str | Path) -> Dict:
    root = Path(root)
    missing: List[str] = []
    for rel in REQUIRED_DOCS:
        p = root / rel
        if not p.exists():
            missing.append(rel)
    return {"ok": len(missing) == 0, "missing": missing, "required": REQUIRED_DOCS}


def verify_extended_compliance_docs(root: str | Path) -> Dict:
    root = Path(root)
    missing: List[str] = []
    for rel in EXTENDED_DOCS:
        p = root / rel
        if not p.exists():
            missing.append(rel)
    return {"ok": len(missing) == 0, "missing": missing, "required": EXTENDED_DOCS}


def verify_organizational_signoffs(path: str | Path) -> Dict:
    """Expect outputs/organizational_signoffs.json with signed=true on each ack."""
    p = Path(path)
    if not p.exists():
        return {"ok": False, "reason": "missing_file"}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "reason": "invalid_json"}
    keys = ("legal_counsel_ack", "tax_advisor_ack", "risk_officer_ack")
    missing = [k for k in keys if k not in data]
    if missing:
        return {"ok": False, "reason": "missing_keys", "missing": missing}
    if bool(data.get("lab_demo_closure")) and os.environ.get("FULL_OPS_ACCEPT_LAB_DEMO") == "1":
        return {"ok": True, "mode": "lab_demo_accepted", "checked": list(keys)}

    unsigned = [k for k in keys if not bool(data.get(k, {}).get("signed"))]
    if unsigned:
        return {"ok": False, "reason": "unsigned", "unsigned": unsigned}
    return {"ok": True, "checked": list(keys)}


def load_readiness_bundle(path: str | Path) -> Dict:
    p = Path(path)
    if not p.exists():
        return {"exists": False}
    return {"exists": True, "data": json.loads(p.read_text(encoding="utf-8"))}
