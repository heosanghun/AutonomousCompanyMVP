"""Run allowlisted MLOps tasks with fail-closed semantics."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agentic.mlops_agent import MLOpsAgentConfig, default_config, run_allowlisted_tasks, write_mlops_agent_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-runs", type=int, default=1)
    parser.add_argument("--timeout-sec", type=int, default=180)
    parser.add_argument("--out", default="outputs/mlops/agent_allowlist_report.json")
    args = parser.parse_args()

    cfg = default_config()
    cfg = MLOpsAgentConfig(
        allowlist=cfg.allowlist,
        max_runs=max(1, int(args.max_runs)),
        timeout_sec=max(30, int(args.timeout_sec)),
    )
    payload = run_allowlisted_tasks(cfg)
    payload["config"] = {
        "max_runs": cfg.max_runs,
        "timeout_sec": cfg.timeout_sec,
        "allowlist": cfg.allowlist,
    }
    payload["profile"] = str(os.environ.get("FULL_OPS_PROFILE", "strict")).lower()
    out = write_mlops_agent_report(payload, args.out)
    print(json.dumps({**payload, "report_path": str(out)}, ensure_ascii=True, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

