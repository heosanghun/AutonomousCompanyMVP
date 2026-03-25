"""Master runner for autonomous-company roadmap progression.

This script intentionally does not execute live trades.
It advances roadmap state only when validation gates pass.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.gate_evaluator import evaluate_phase_gate
from src.ops.report_builder import build_daily_report, build_weekly_report
from src.ops.state_manager import append_history, load_json, load_or_init_state, save_json, save_state


def _run(cmd: list[str]) -> int:
    return subprocess.run(cmd, cwd=str(ROOT), check=False).returncode


def _now_tag() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%d")


def main() -> int:
    plan_path = ROOT / "configs" / "master_plan.json"
    state_path = ROOT / "outputs" / "roadmap_state.json"
    phase_status_path = ROOT / "outputs" / "phase_status.json"
    daily_reports_dir = ROOT / "outputs" / "reports" / "daily"
    weekly_report_path = ROOT / "outputs" / "reports" / "weekly_report.md"
    validation_report_path = ROOT / "outputs" / "validation_report.json"
    validation_summary_path = ROOT / "outputs" / "validation_run" / "summary.json"

    plan = load_json(plan_path)
    state = load_or_init_state(state_path)
    phases = plan.get("phases", [])
    completion_path = ROOT / "outputs" / "final_completion_report.json"

    if state.current_phase_index >= len(phases):
        append_history(state, {"event": "all_phases_completed"})
        save_state(state_path, state)
        completion_payload = {
            "goal": plan.get("goal"),
            "status": "completed",
            "completed_phases": state.completed_phases,
            "current_phase_index": state.current_phase_index,
            "completed_at_utc": datetime.now(tz=timezone.utc).isoformat(),
            "artifacts": {
                "roadmap_state": str(state_path),
                "phase_status": str(phase_status_path),
                "weekly_report": str(weekly_report_path),
                "validation_summary": str(validation_summary_path),
            },
        }
        save_json(completion_path, completion_payload)
        print(json.dumps(completion_payload, ensure_ascii=True, indent=2))
        return 0

    phase = phases[state.current_phase_index]
    phase_id = phase["id"]
    phase_name = phase["name"]
    criteria = phase.get("success_criteria", {})

    append_history(state, {"event": "phase_run_started", "phase_id": phase_id, "phase_name": phase_name})
    save_state(state_path, state)

    rc_validate = _run([sys.executable, str(ROOT / "scripts" / "validate_gates.py")])
    if rc_validate != 0:
        append_history(
            state,
            {"event": "phase_validation_script_failed", "phase_id": phase_id, "return_code": rc_validate},
        )
        save_state(state_path, state)
        return rc_validate

    validation_report = json.loads(validation_report_path.read_text(encoding="utf-8"))
    summary = json.loads(validation_summary_path.read_text(encoding="utf-8"))
    summary["validation_ok"] = bool(validation_report.get("ok", False))

    passed, details = evaluate_phase_gate(summary, criteria)
    save_json(
        phase_status_path,
        {
            "phase_id": phase_id,
            "phase_name": phase_name,
            "passed": passed,
            "details": details,
            "checked_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        },
    )

    daily_path = daily_reports_dir / f"daily_{_now_tag()}.md"
    notes = [f"phase_id={phase_id}", f"phase_name={phase_name}", f"gate_passed={passed}"]
    if not passed:
        notes.append(f"gate_fail_reasons={details.get('reasons', [])}")
    build_daily_report(validation_summary_path, daily_path, notes)
    build_weekly_report(daily_reports_dir, weekly_report_path)

    if passed:
        state.completed_phases.append(phase_id)
        state.current_phase_index += 1
        append_history(state, {"event": "phase_completed", "phase_id": phase_id})
    else:
        append_history(state, {"event": "phase_blocked", "phase_id": phase_id, "reasons": details.get("reasons", [])})
    save_state(state_path, state)

    print(
        json.dumps(
            {
                "phase_id": phase_id,
                "phase_name": phase_name,
                "passed": passed,
                "next_phase_index": state.current_phase_index,
                "daily_report": str(daily_path),
                "weekly_report": str(weekly_report_path),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
