"""Continuously run live-readiness and limited-live validation until pass."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    return proc.returncode


def main() -> int:
    out_dir = ROOT / "outputs" / "live_worker"
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / "state.json"
    retry_sec = 300
    while True:
        _run(["python", "scripts/finalize_live_readiness.py"])
        _run(["python", "scripts/verify_production_readiness.py"])
        rc = _run(["python", "scripts/run_limited_live_validation.py"])
        report_path = ROOT / "outputs" / "limited_live_validation_report.json"
        report = {}
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
        state = {
            "last_run_ok": rc == 0,
            "passed": bool(report.get("passed", False)),
            "credentials_present": bool(report.get("credentials_present", False)),
            "filled_ratio": float(report.get("filled_ratio", 0.0)),
            "timestamp_epoch": time.time(),
        }
        state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
        if rc == 0:
            return 0
        time.sleep(retry_sec)


if __name__ == "__main__":
    raise SystemExit(main())
