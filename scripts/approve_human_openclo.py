"""Approve openclo pilot execution (human gate artifact)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--by", required=True, help="approver name")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    path = ROOT / "outputs" / "human_openclo_approval.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "approved": True,
        "approved_by": args.by,
        "scope": "openclo_pilot_sandbox_only",
        "approved_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "notes": args.notes,
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
