"""Proposal-only operations copilot (no execution side effects)."""

from __future__ import annotations

from typing import Any, Dict, List


REMEDIATION = {
    "missing_compliance_docs": "Run bootstrap compliance bundle and attach required legal docs.",
    "missing_readiness_bundle": "Generate readiness bundle before production verification.",
    "live_not_approved_in_bundle": "Set live_trading_approved=true only after governance approval.",
    "invalid_bundle_approver_for_strict": "Use a real human approver identity in strict profile.",
    "missing_live_guard_flag": "Create outputs/live_readiness_approved.flag after sign-off.",
    "missing_or_unapproved_human_live_approval": "Fill and approve outputs/human_live_approval.json.",
    "drift_detected": "Keep execution conservative; retrain/recalibrate before live expansion.",
    "reconcile_check_failed": "Run reconcile script and inspect fills/run_id mismatch.",
}


def propose_next_actions(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return action proposals only; never execute.
    Expected input: {"errors":[...], "gates":{...}, "risk":{...}}
    """
    errors = context.get("errors", []) if isinstance(context, dict) else []
    gates = context.get("gates", {}) if isinstance(context, dict) else {}
    proposals: List[Dict[str, Any]] = []

    for err in errors:
        text = REMEDIATION.get(str(err), f"Investigate and remediate: {err}")
        proposals.append(
            {
                "priority": "P0" if "missing" in str(err) or "failed" in str(err) else "P1",
                "trigger": str(err),
                "action": text,
                "evidence_required": "Attach command output or artifact path before closure.",
            }
        )

    for k, v in gates.items():
        if not bool(v):
            proposals.append(
                {
                    "priority": "P1",
                    "trigger": f"gate:{k}",
                    "action": f"Resolve failing gate `{k}` and re-run validation pipeline.",
                    "evidence_required": "Updated report JSON with pass status.",
                }
            )

    if not proposals:
        proposals.append(
            {
                "priority": "P2",
                "trigger": "steady_state",
                "action": "No blocking issues. Continue periodic checks and keep strict profile.",
                "evidence_required": "Latest validation reports remain green.",
            }
        )

    return {
        "mode": "proposal_only",
        "count": len(proposals),
        "proposals": proposals,
    }

