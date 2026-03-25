"""Operational gate checks for MVP promotion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agentic.propose_agent import propose_next_actions
from src.main import run


def validate(summary: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    metrics = summary["metrics"]

    if metrics["latency_p99_ms"] > 5.0:
        errors.append("p99 latency exceeds 5ms threshold")
    if metrics["mdd"] > 0.15:
        errors.append("MDD exceeds 15% safety threshold")
    if summary["kill_switch"]:
        errors.append("kill-switch triggered during validation run")
    if summary["n_updates"] <= 0:
        errors.append("no slow-loop policy update observed")
    if int(summary.get("n_fills", 0)) <= 0:
        errors.append("no execution fills were generated")
    fills_path = Path("outputs/validation_run/fills.jsonl")
    if not fills_path.exists():
        errors.append("fills artifact missing: outputs/validation_run/fills.jsonl")
    drift = summary.get("drift", {})
    if bool(drift.get("drift_detected", False)):
        errors.append("drift detected: runtime should remain in guarded mode")
    if not bool(summary.get("reconcile", {}).get("ok", False)):
        errors.append("reconcile check failed")
    mlops_artifact = Path("outputs/mlops/pipeline_result.json")
    if not mlops_artifact.exists():
        errors.append("mlops pipeline artifact missing: outputs/mlops/pipeline_result.json")
    else:
        try:
            mlops_ok = bool(json.loads(mlops_artifact.read_text(encoding="utf-8")).get("ok", False))
            if not mlops_ok:
                errors.append("mlops pipeline artifact indicates failure")
        except Exception:
            errors.append("mlops pipeline artifact unreadable")

    return len(errors) == 0, errors


def main() -> int:
    from scripts.run_mlops_data_pipeline import main as run_mlops_main

    run_mlops_main()
    out_dir = "outputs/validation_run"
    summary = run(output_dir=out_dir)
    ok, errors = validate(summary)
    report = {
        "ok": ok,
        "errors": errors,
        "summary_path": str(Path(out_dir) / "summary.json"),
        "audit_path": str(Path(out_dir) / "audit.log"),
        "proposal_copilot": propose_next_actions({"errors": errors, "gates": summary.get("reconcile", {})}),
    }
    report_path = Path("outputs/validation_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
