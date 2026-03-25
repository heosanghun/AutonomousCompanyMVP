"""Read-only observation agent utilities for operations status."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ObserveSummary:
    health: str
    highlights: List[str]
    anomalies: List[str]
    explain: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "health": self.health,
            "highlights": self.highlights,
            "anomalies": self.anomalies,
            "explain": self.explain,
        }


def summarize_status(status_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create deterministic, read-only status summary from monitoring payload."""
    summary = status_payload.get("summary", {}) if isinstance(status_payload, dict) else {}
    metrics = status_payload.get("metrics", {}) if isinstance(status_payload, dict) else {}
    gates = status_payload.get("gates", {}) if isinstance(status_payload, dict) else {}
    drift = summary.get("drift", {}) if isinstance(summary, dict) else {}

    pass_cnt = 0
    fail_cnt = 0
    for v in gates.values():
        if bool(v):
            pass_cnt += 1
        else:
            fail_cnt += 1

    anomalies: List[str] = []
    if fail_cnt > 0:
        anomalies.append(f"gate_failures={fail_cnt}")
    if bool(drift.get("drift_detected", False)):
        anomalies.append("drift_detected")
    if bool(summary.get("kill_switch", False)):
        anomalies.append("kill_switch_on")
    if float(metrics.get("latency_p99_ms") or 0.0) > 5.0:
        anomalies.append("latency_p99_over_5ms")

    if anomalies:
        health = "degraded"
    else:
        health = "healthy"

    highlights = [
        f"sharpe={metrics.get('sharpe')}",
        f"win_rate={metrics.get('win_rate')}",
        f"fills={summary.get('n_fills')}",
        f"gates_pass={pass_cnt}",
    ]

    explain = (
        "Read-only observe agent analyzed status payload without executing actions. "
        f"health={health}, anomalies={len(anomalies)}."
    )
    return ObserveSummary(health=health, highlights=highlights, anomalies=anomalies, explain=explain).as_dict()

