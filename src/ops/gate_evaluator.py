"""Evaluate phase gate status from validation summary."""

from __future__ import annotations

from typing import Any, Dict, Tuple


def evaluate_phase_gate(summary: Dict[str, Any], criteria: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    metrics = summary.get("metrics", {})
    reasons = []

    if bool(summary.get("kill_switch")) != bool(criteria.get("kill_switch", False)):
        reasons.append("kill-switch state does not match required criteria")

    if bool(summary.get("validation_ok", True)) != bool(criteria.get("validation_ok", True)):
        reasons.append("validation_ok mismatch")

    mdd_max = float(criteria.get("mdd_max", 1.0))
    if float(metrics.get("mdd", 1.0)) > mdd_max:
        reasons.append(f"mdd above limit ({metrics.get('mdd')} > {mdd_max})")

    latency_limit = float(criteria.get("latency_p99_ms_max", 999.0))
    if float(metrics.get("latency_p99_ms", 999.0)) > latency_limit:
        reasons.append(
            f"latency_p99_ms above limit ({metrics.get('latency_p99_ms')} > {latency_limit})"
        )

    return len(reasons) == 0, {"reasons": reasons, "criteria": criteria, "metrics": metrics}
