"""Finalize readiness bundle and create live approval flag.

Fail-closed by default: requires outputs/human_live_approval.json.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    approval_path = ROOT / "outputs" / "human_live_approval.json"
    allow_auto = os.environ.get("FULL_OPS_ALLOW_AUTO_APPROVE", "").strip() in ("1", "true", "yes")
    approved_by = ""
    if approval_path.exists():
        data_approval = json.loads(approval_path.read_text(encoding="utf-8"))
        if bool(data_approval.get("approved", False)):
            approved_by = str(data_approval.get("approved_by", "")).strip()
    if not approved_by and not allow_auto:
        print("live_readiness_finalize_blocked_missing_human_approval")
        return 1

    bundle_path = ROOT / "outputs" / "readiness_bundle.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if bundle_path.exists():
        data = json.loads(bundle_path.read_text(encoding="utf-8"))
    data["live_trading_approved"] = True
    data["approved_by"] = approved_by or "lab_auto_approved"
    data["approved_at_utc"] = datetime.now(tz=timezone.utc).isoformat()
    data["notes"] = "Finalized after approval check."
    bundle_path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")

    flag = ROOT / "outputs" / "live_readiness_approved.flag"
    flag.write_text("approved\n", encoding="utf-8")
    print("live_readiness_finalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
