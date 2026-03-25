"""Create human live approval template (fail-closed approval artifact)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = ROOT / "outputs" / "human_live_approval.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        payload = {
            "approved": False,
            "approved_by": "",
            "approved_at_utc": "",
            "notes": "Set approved=true and approved_by to a real human approver.",
        }
        p.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
