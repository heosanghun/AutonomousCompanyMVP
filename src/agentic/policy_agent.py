"""Policy proposal agent for System2 (proposal-only, no direct apply)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PolicyProposal:
    slow_interval_steps: int
    force_trigger_volatility: float
    force_trigger_imbalance: float
    rationale: str

    def as_dict(self) -> Dict:
        return {
            "slow_interval_steps": int(self.slow_interval_steps),
            "force_trigger_volatility": float(self.force_trigger_volatility),
            "force_trigger_imbalance": float(self.force_trigger_imbalance),
            "rationale": self.rationale,
            "mode": "proposal_only",
        }


def propose_system2_policy(latency_p99_ms: float, drift_detected: bool) -> Dict:
    """
    Generate conservative policy update proposal.
    Does not apply config; only outputs candidate values.
    """
    slow_interval = 40
    force_vol = 0.03
    force_imb = 0.30
    notes = []

    if latency_p99_ms > 5.0:
        # Reduce planning frequency when runtime is under pressure.
        slow_interval = 60
        notes.append("increase slow_interval due to high latency")
    if drift_detected:
        # Trigger System2 more aggressively when drift appears.
        force_vol = 0.02
        force_imb = 0.20
        notes.append("lower force triggers due to drift")
    if not notes:
        notes.append("keep baseline configuration")

    return PolicyProposal(
        slow_interval_steps=slow_interval,
        force_trigger_volatility=force_vol,
        force_trigger_imbalance=force_imb,
        rationale="; ".join(notes),
    ).as_dict()

