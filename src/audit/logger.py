"""Audit logging with optional hash chain for tamper-evidence."""

from __future__ import annotations

import hashlib
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
    def __init__(self, path: str | Path, enable_hash_chain: bool = True) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.enable_hash_chain = enable_hash_chain

    def _last_chain_hash(self) -> str:
        if not self.path.exists():
            return ""
        lines = self.path.read_text(encoding="utf-8").splitlines()
        if not lines:
            return ""
        try:
            obj = json.loads(lines[-1])
            return str(obj.get("chain_hash", "") or "")
        except Exception:
            return ""

    def log(self, stage: str, payload: Dict[str, Any]) -> None:
        event = AuditEvent(
            ts=datetime.now(tz=timezone.utc).isoformat(),
            stage=stage,
            payload=payload,
        )
        base = asdict(event)
        if not self.enable_hash_chain:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(base, ensure_ascii=True) + "\n")
            return
        prev = self._last_chain_hash()
        canonical = json.dumps(base, sort_keys=True, ensure_ascii=True)
        chain_hash = hashlib.sha256((prev + canonical).encode("utf-8")).hexdigest()
        record = {"chain_prev": prev, "chain_hash": chain_hash, **base}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")
