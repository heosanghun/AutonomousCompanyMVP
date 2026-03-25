"""Autonomous worker loop for continuous roadmap execution.

This worker repeatedly runs master validation/progression and performs
basic self-healing actions (retry/backoff/logging) without user interaction.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "worker"
OUT.mkdir(parents=True, exist_ok=True)
WORKER_LOG = OUT / "worker.log"
WORKER_STATE = OUT / "worker_state.json"
ROADMAP_STATE = ROOT / "outputs" / "roadmap_state.json"
MASTER_PLAN = ROOT / "configs" / "master_plan.json"


def _utc() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _log(msg: str) -> None:
    line = f"[{_utc()}] {msg}"
    with WORKER_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def _save_state(payload: dict) -> None:
    WORKER_STATE.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _is_goal_completed() -> bool:
    if not ROADMAP_STATE.exists() or not MASTER_PLAN.exists():
        return False
    state = json.loads(ROADMAP_STATE.read_text(encoding="utf-8"))
    plan = json.loads(MASTER_PLAN.read_text(encoding="utf-8"))
    phases = plan.get("phases", [])
    return int(state.get("current_phase_index", 0)) >= len(phases)


def run_once() -> tuple[bool, str]:
    cmd = [sys.executable, str(ROOT / "scripts" / "run_autonomous_master.py")]
    proc = subprocess.run(cmd, cwd=str(ROOT), check=False, capture_output=True, text=True)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if proc.returncode == 0:
        return True, stdout
    return False, f"returncode={proc.returncode}\nstdout={stdout}\nstderr={stderr}"


def main() -> int:
    # Conservative default loop interval.
    interval_sec = 900  # 15 minutes
    max_consecutive_failures = 5
    consecutive_failures = 0
    total_runs = 0

    _log("autonomous_worker_started")
    while True:
        if _is_goal_completed():
            _log("goal_completed_worker_stopping")
            _save_state(
                {
                    "status": "completed",
                    "consecutive_failures": consecutive_failures,
                    "total_runs": total_runs,
                    "updated_at_utc": _utc(),
                }
            )
            return 0

        total_runs += 1
        ok, detail = run_once()
        if ok:
            consecutive_failures = 0
            _log(f"run_success #{total_runs}")
            if detail:
                _log(f"run_output: {detail[:1000]}")
        else:
            consecutive_failures += 1
            _log(f"run_failed #{total_runs} failures={consecutive_failures} detail={detail[:1200]}")

            # Basic self-healing: retry quickly on transient failures.
            if consecutive_failures < max_consecutive_failures:
                _log("retry_in_60s")
                _save_state(
                    {
                        "status": "retrying",
                        "consecutive_failures": consecutive_failures,
                        "total_runs": total_runs,
                        "updated_at_utc": _utc(),
                    }
                )
                time.sleep(60)
                continue

            # Escalation mode: longer cool-down to avoid thrashing.
            _log("escalation_mode_cooldown_30m")
            _save_state(
                {
                    "status": "escalated_cooldown",
                    "consecutive_failures": consecutive_failures,
                    "total_runs": total_runs,
                    "updated_at_utc": _utc(),
                }
            )
            time.sleep(1800)
            continue

        _save_state(
            {
                "status": "healthy",
                "consecutive_failures": consecutive_failures,
                "total_runs": total_runs,
                "updated_at_utc": _utc(),
                "next_run_in_sec": interval_sec,
            }
        )
        time.sleep(interval_sec)


if __name__ == "__main__":
    raise SystemExit(main())
