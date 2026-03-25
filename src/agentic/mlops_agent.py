"""Low-risk MLOps automation agent with allowlist and fail-closed behavior."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class MLOpsAgentConfig:
    allowlist: List[str]
    max_runs: int = 1
    timeout_sec: int = 120


def run_allowlisted_tasks(config: MLOpsAgentConfig) -> Dict:
    results: List[Dict] = []
    if config.max_runs <= 0:
        return {"ok": False, "reason": "max_runs_must_be_positive", "results": []}

    for cmd in config.allowlist[: config.max_runs]:
        started = time.time()
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=config.timeout_sec,
            )
            elapsed = round(time.time() - started, 3)
            rec = {
                "cmd": cmd,
                "returncode": int(proc.returncode),
                "elapsed_sec": elapsed,
                "stdout_tail": (proc.stdout or "")[-1000:],
                "stderr_tail": (proc.stderr or "")[-1000:],
            }
            results.append(rec)
            # fail-closed: stop immediately on first failure
            if proc.returncode != 0:
                return {"ok": False, "reason": "task_failed", "results": results}
        except subprocess.TimeoutExpired:
            return {"ok": False, "reason": "task_timeout", "results": results}
        except Exception as e:
            return {"ok": False, "reason": f"task_error:{type(e).__name__}", "results": results}
    return {"ok": True, "reason": "all_tasks_passed", "results": results}


def write_mlops_agent_report(payload: Dict, out_path: str | Path) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return p


def default_config() -> MLOpsAgentConfig:
    # Keep explicit interpreter for cross-shell reliability.
    py = sys.executable
    return MLOpsAgentConfig(
        allowlist=[
            f'"{py}" scripts/run_mlops_data_pipeline.py',
        ],
        max_runs=1,
        timeout_sec=180,
    )

