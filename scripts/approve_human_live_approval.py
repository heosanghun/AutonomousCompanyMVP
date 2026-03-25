"""Approve human live approval artifact with signer name."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--by", required=True, help="Human approver name/id")
    parser.add_argument("--notes", default="manual strict approval")
    args = parser.parse_args()
    p = ROOT / "outputs" / "human_live_approval.json"
    if not p.exists():
        print("missing_human_live_approval_json")
        return 1
    data = json.loads(p.read_text(encoding="utf-8"))
    data["approved"] = True
    data["approved_by"] = args.by.strip()
    data["approved_at_utc"] = datetime.now(tz=timezone.utc).isoformat()
    data["notes"] = args.notes
    p.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    print(str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
