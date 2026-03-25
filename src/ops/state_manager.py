"""State manager for long-horizon autonomous execution roadmap."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class RoadmapState:
    current_phase_index: int
    completed_phases: List[str]
    history: List[Dict[str, Any]]


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def load_or_init_state(path: str | Path) -> RoadmapState:
    p = Path(path)
    if not p.exists():
        state = RoadmapState(current_phase_index=0, completed_phases=[], history=[])
        save_state(p, state)
        return state
    raw = load_json(p)
    return RoadmapState(
        current_phase_index=int(raw.get("current_phase_index", 0)),
        completed_phases=list(raw.get("completed_phases", [])),
        history=list(raw.get("history", [])),
    )


def save_state(path: str | Path, state: RoadmapState) -> None:
    save_json(
        Path(path),
        {
            "current_phase_index": state.current_phase_index,
            "completed_phases": state.completed_phases,
            "history": state.history,
            "updated_at_utc": utc_now_iso(),
        },
    )


def append_history(state: RoadmapState, event: Dict[str, Any]) -> None:
    event = dict(event)
    event["ts_utc"] = utc_now_iso()
    state.history.append(event)
