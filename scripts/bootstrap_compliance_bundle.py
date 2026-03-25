"""Create baseline compliance docs and readiness bundle template."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


DOCS = {
    "docs/compliance/kyc_aml_checklist.md": [
        "# KYC/AML Checklist",
        "",
        "- [ ] Jurisdiction identified",
        "- [ ] Exchange KYC status verified",
        "- [ ] AML monitoring policy documented",
    ],
    "docs/compliance/tax_reporting_checklist.md": [
        "# Tax Reporting Checklist",
        "",
        "- [ ] Tax residency confirmed",
        "- [ ] Trade ledger export process documented",
        "- [ ] Monthly tax summary workflow configured",
    ],
    "docs/compliance/security_controls_checklist.md": [
        "# Security Controls Checklist",
        "",
        "- [ ] API keys least privilege",
        "- [ ] Secret rotation policy enabled",
        "- [ ] Access review schedule documented",
    ],
    "docs/compliance/incident_response_runbook.md": [
        "# Incident Response Runbook",
        "",
        "- [ ] SEV levels defined",
        "- [ ] On-call escalation path set",
        "- [ ] Kill-switch procedure validated",
        "- [ ] Post-incident review template ready",
        "- [ ] Customer/regulator notification policy (if applicable)",
    ],
    "docs/compliance/regulatory_scope.md": [
        "# Regulatory Scope (template)",
        "",
        "- [ ] Primary jurisdiction(s) for the operating entity",
        "- [ ] Whether activity is VASP / securities / derivatives (legal determination)",
        "- [ ] Registration or licensing obligations identified",
        "- [ ] Record retention period for trade and decision logs",
        "- [ ] Named responsible human officer for compliance questions",
    ],
    "docs/compliance/organizational_raci.md": [
        "# RACI — Autonomous Trading & Operations",
        "",
        "| Activity | Responsible | Accountable | Consulted | Informed |",
        "|----------|-------------|-------------|-----------|----------|",
        "| Live trading enable | Eng | Risk officer | Legal | Exec |",
        "| Kill-switch / incident | Eng on-call | Risk officer | Legal | Exec |",
        "| Model/strategy change | Eng | Risk officer | — | Exec |",
        "",
        "Replace names and dates; code cannot substitute human accountability.",
    ],
    "docs/compliance/capital_and_risk_limits.md": [
        "# Capital & Risk Limits (template)",
        "",
        "- [ ] Max capital at risk (notional / margin) per venue",
        "- [ ] Max daily / weekly loss vs. equity",
        "- [ ] Position and leverage caps per symbol",
        "- [ ] Human approval threshold for limit changes (see configs/human_approval_policy.json)",
        "- [ ] Review cadence (weekly / monthly)",
    ],
}


def main() -> int:
    for rel, lines in DOCS.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    bundle = ROOT / "outputs" / "readiness_bundle.json"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    if not bundle.exists():
        bundle.write_text(
            json.dumps(
                {
                    "live_trading_approved": False,
                    "approved_by": "",
                    "approved_at_utc": "",
                    "notes": "Set live_trading_approved=true only after external legal/security sign-off.",
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )
    print("bootstrap_compliance_bundle_done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
