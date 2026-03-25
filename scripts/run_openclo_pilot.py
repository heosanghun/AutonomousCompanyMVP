"""Pilot open-closed-loop execution agent with sandbox + approval + allowlist."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bootstrap_env import load_dotenv_files


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_actions(path: Path) -> list[dict[str, Any]]:
    obj = _read_json(path)
    actions = obj.get("actions", []) if isinstance(obj, dict) else []
    return [a for a in actions if isinstance(a, dict) and str(a.get("id", "")).strip()]


def _approval_ok() -> bool:
    approval = _read_json(ROOT / "outputs" / "human_openclo_approval.json")
    return bool(approval.get("approved")) and bool(str(approval.get("approved_by", "")).strip())


def _build_status_snapshot() -> dict[str, Any]:
    summary = _read_json(ROOT / "outputs" / "summary.json")
    gates = _read_json(ROOT / "outputs" / "full_operational_gate_report.json")
    return {
        "execution_mode": summary.get("execution_mode"),
        "kill_switch": summary.get("kill_switch"),
        "metrics": (summary.get("metrics") if isinstance(summary, dict) else {}) or {},
        "gates_ok": bool(gates.get("ok", False)),
    }


def _plan_ids(goal: str, status: dict[str, Any], actions: list[dict[str, Any]], max_actions: int) -> list[str]:
    allowed = {str(a["id"]): a for a in actions}
    picks: list[str] = []
    g = (goal or "").lower()
    if status.get("gates_ok") is False or "게이트" in g or "gate" in g:
        picks.extend(["refresh_status", "validate_gates", "verify_readiness"])
    elif "mlops" in g or "데이터" in g or "pipeline" in g:
        picks.extend(["refresh_status", "run_mlops_allowlist"])
    else:
        picks.extend(["refresh_status", "limited_execution_dryrun"])
    out: list[str] = []
    for pid in picks:
        if pid in allowed and pid not in out:
            out.append(pid)
        if len(out) >= max_actions:
            break
    return out


def _run_action(action: dict[str, Any], sandbox: bool) -> dict[str, Any]:
    cmd = str(action.get("command", "")).replace("{python}", sys.executable)
    timeout = int(action.get("timeout_sec", 90))
    env = os.environ.copy()
    env["EXECUTION_MODE"] = "paper"
    env["OPENCLO_SANDBOX"] = "1" if sandbox else "0"
    env["AGENTIC_EXECUTION_MODE"] = "openclo_pilot"
    started = datetime.now(tz=timezone.utc).isoformat()
    proc = subprocess.run(
        cmd,
        shell=True,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "id": action.get("id"),
        "command": cmd,
        "started_at_utc": started,
        "returncode": int(proc.returncode),
        "stdout_tail": (proc.stdout or "")[-1200:],
        "stderr_tail": (proc.stderr or "")[-1200:],
        "timeout_sec": timeout,
    }


def main() -> int:
    load_dotenv_files(ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", default="현재 운영 리스크를 안전하게 진단하고 보완")
    parser.add_argument("--allowlist", default="configs/openclo_pilot_allowlist.json")
    parser.add_argument("--max-actions", type=int, default=3)
    parser.add_argument("--sandbox", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--require-approval", action="store_true")
    parser.add_argument("--out", default="outputs/agentic/openclo_pilot_report.json")
    args = parser.parse_args()

    if not args.sandbox:
        print(json.dumps({"ok": False, "reason": "sandbox_required"}, ensure_ascii=True, indent=2))
        return 1
    if args.require_approval and not _approval_ok() and not args.dry_run:
        print(json.dumps({"ok": False, "reason": "missing_human_openclo_approval"}, ensure_ascii=True, indent=2))
        return 1

    allowlist_path = ROOT / args.allowlist
    actions = _load_actions(allowlist_path)
    if not actions:
        print(json.dumps({"ok": False, "reason": "empty_allowlist"}, ensure_ascii=True, indent=2))
        return 1

    status = _build_status_snapshot()
    plan_ids = _plan_ids(args.goal, status, actions, max(1, int(args.max_actions)))
    action_by_id = {str(a["id"]): a for a in actions}
    planned = [action_by_id[x] for x in plan_ids if x in action_by_id]

    report: dict[str, Any] = {
        "ok": True,
        "mode": "openclo_pilot",
        "sandbox": True,
        "dry_run": bool(args.dry_run),
        "approval_required": bool(args.require_approval),
        "approval_ok": _approval_ok(),
        "goal": args.goal,
        "status_snapshot": status,
        "planned_action_ids": [a.get("id") for a in planned],
        "results": [],
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
    }

    if not args.dry_run:
        for a in planned:
            rec = _run_action(a, sandbox=True)
            report["results"].append(rec)
            if rec.get("returncode", 1) != 0:
                report["ok"] = False
                report["reason"] = "action_failed"
                break

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
