"""Append-only experiment registry (JSONL) without external MLflow server."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def append_experiment(
    name: str,
    payload: Dict[str, Any],
    *,
    run_id: str = "",
    out_dir: str | Path = "outputs/mlops",
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "experiments.jsonl"
    line = {
        "ts_utc": utc_now_iso(),
        "name": name,
        "run_id": run_id,
        **payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=True) + "\n")
    return path
