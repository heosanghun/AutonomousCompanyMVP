"""Bootstrap extended compliance docs, org signoffs template, and optional lab-demo closure."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write_org_signoffs(lab_demo: bool) -> None:
    path = ROOT / "outputs" / "organizational_signoffs.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=timezone.utc).isoformat()
    if lab_demo:
        data = {
            "jurisdiction": "LAB_DEMO_NOT_PRODUCTION",
            "lab_demo_closure": True,
            "closure_disclaimer": "LAB_DEMO_ONLY_NOT_LEGAL_OR_TAX_ADVICE",
            "legal_counsel_ack": {"signed": True, "by": "lab_automation", "at_utc": now},
            "tax_advisor_ack": {"signed": True, "by": "lab_automation", "at_utc": now},
            "risk_officer_ack": {"signed": True, "by": "lab_automation", "at_utc": now},
            "notes": "Replace with real human sign-offs before production; set lab_demo_closure false.",
        }
    else:
        data = {
            "jurisdiction": "",
            "lab_demo_closure": False,
            "closure_disclaimer": "",
            "legal_counsel_ack": {"signed": False, "by": "", "at_utc": ""},
            "tax_advisor_ack": {"signed": False, "by": "", "at_utc": ""},
            "risk_officer_ack": {"signed": False, "by": "", "at_utc": ""},
            "notes": "Physical persons must complete; code cannot substitute.",
        }
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lab-demo-signoffs",
        action="store_true",
        help="Write organizational_signoffs.json with lab flags (not a legal substitute).",
    )
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "bootstrap_compliance_bundle.py")], check=False)
    _write_org_signoffs(lab_demo=args.lab_demo_signoffs)
    print("bootstrap_full_operations_done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
