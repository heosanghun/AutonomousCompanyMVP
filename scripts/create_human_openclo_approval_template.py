"""Create approval template for openclo pilot execution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    path = ROOT / "outputs" / "human_openclo_approval.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "approved": False,
        "approved_by": "",
        "scope": "openclo_pilot_sandbox_only",
        "created_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "notes": "Set approved=true and approved_by to allow non-dry-run pilot execution.",
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
