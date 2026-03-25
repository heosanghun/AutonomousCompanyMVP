"""Basic reconcile checks between internal and execution artifacts."""

from __future__ import annotations

import json
from pathlib import Path


def _count_jsonl(path: Path, run_id: str | None) -> int:
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if run_id is None:
            n += 1
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if str(obj.get("run_id", "") or "") == run_id:
            n += 1
    return n


def reconcile_counts(outputs_dir: str | Path) -> dict:
    out = Path(outputs_dir)
    summary_path = out / "summary.json"
    fills_path = out / "fills.jsonl"
    live_fills_path = out / "live_fills.jsonl"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected = int(summary.get("n_fills", 0))
    rid = str(summary.get("run_id", "") or "").strip()
    run_filter: str | None = rid if rid else None
    observed = _count_jsonl(fills_path, run_filter) + _count_jsonl(live_fills_path, run_filter)
    return {
        "ok": observed >= expected,
        "expected_n_fills": expected,
        "observed_n_fills": observed,
        "run_id": rid,
        "fills_jsonl": str(fills_path),
        "live_fills_jsonl": str(live_fills_path),
    }
