"""Enforces operational limits against human approval policy thresholds."""

import json
from pathlib import Path


def enforce_policy_limits(
    limits_path: str | Path = "configs/operational_limits.json",
    policy_path: str | Path = "configs/human_approval_policy.json",
    approval_path: str | Path = "outputs/human_live_approval.json",
) -> tuple[bool, list[str]]:
    """Checks if operational limits exceed policy thresholds without explicit human approval."""
    limits_file = Path(limits_path)
    policy_file = Path(policy_path)
    approval_file = Path(approval_path)

    errors = []

    if not policy_file.exists():
        return True, []  # No policy to enforce

    if not limits_file.exists():
        return True, []  # No limits to check

    try:
        limits = json.loads(limits_file.read_text(encoding="utf-8"))
        policy = json.loads(policy_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, [f"Failed to parse config JSON: {e}"]

    # Policy threshold for notional
    notional_threshold = float(policy.get("notional_increase_requires_approval_above_usd", 1000.0))
    current_notional = float(limits.get("max_open_notional_usd", 0.0))
    current_order_notional = float(limits.get("max_notional_usd_per_order", 0.0))

    needs_approval = False
    reasons = []

    if current_notional > notional_threshold:
        needs_approval = True
        reasons.append(f"max_open_notional_usd ({current_notional}) exceeds threshold ({notional_threshold})")

    if current_order_notional > notional_threshold:
        needs_approval = True
        reasons.append(f"max_notional_usd_per_order ({current_order_notional}) exceeds threshold ({notional_threshold})")

    if needs_approval:
        if not approval_file.exists():
            errors.append(f"Human approval required but {approval_path} is missing. Reasons: {', '.join(reasons)}")
        else:
            try:
                approval = json.loads(approval_file.read_text(encoding="utf-8"))
                if approval.get("status") != "approved":
                    errors.append(f"Human approval file exists but status is not 'approved'. Reasons: {', '.join(reasons)}")
            except Exception:
                errors.append(f"Failed to read human approval file {approval_path}. Reasons: {', '.join(reasons)}")

    return len(errors) == 0, errors
