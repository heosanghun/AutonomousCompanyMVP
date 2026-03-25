"""Simple audit logging for decision traceability."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


@dataclass
class AuditEvent:
    ts: str
    stage: str
    payload: Dict[str, Any]


class AuditLogger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, stage: str, payload: Dict[str, Any]) -> None:
        event = AuditEvent(
            ts=datetime.now(tz=timezone.utc).isoformat(),
            stage=stage,
            payload=payload,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=True) + "\n")
