"""Print autonomous worker health and roadmap completion status."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
worker_state = ROOT / "outputs" / "worker" / "worker_state.json"
roadmap_state = ROOT / "outputs" / "roadmap_state.json"
final_report = ROOT / "outputs" / "final_completion_report.json"


def _load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    payload = {
        "worker_state": _load(worker_state),
        "roadmap_state": _load(roadmap_state),
        "final_completion_report": _load(final_report),
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
