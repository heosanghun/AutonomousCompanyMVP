# AutonomousCompanyMVP

Autonomous-company MVP centered on automated-trading as the first revenue engine.

## Environment

Optional local secrets: create `.env` or `.ENV` in the project root (see `.env.example`).  
`python -m src.main` loads these files into the process environment before running.  
Do not commit real keys; `.env` and `.ENV` are gitignored.

Test Gemini key (does not print the key): `python scripts/test_gemini_api.py`

## Quick Start

```bash
python scripts/bootstrap_compliance_bundle.py
python -m src.main
python scripts/validate_gates.py
python scripts/run_autonomous_master.py
```

## Continuous Autonomous Mode

Run continuous self-validation and roadmap progression loop:

```bash
python scripts/autonomous_worker.py
```

Windows background start:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_worker.ps1
```

Windows startup auto-run (worker + monitoring server):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_startup_tasks.ps1
```

Remove startup tasks:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall_startup_tasks.ps1
```

Worker/roadmap status:

```bash
python scripts/worker_status.py
```

Artifacts:

- `outputs/worker/worker.log`
- `outputs/worker/worker_state.json`
- `outputs/final_completion_report.json`

## What Runs

- `src.main`: runs the local simulation runtime and writes summary/audit artifacts.
- `scripts/validate_gates.py`: checks operation gates (risk, latency, kill-switch).
- `scripts/run_autonomous_master.py`: advances roadmap phases only when gates pass.

## Core Artifacts

- `outputs/summary.json`
- `outputs/validation_report.json`
- `outputs/validation_run/summary.json`
- `outputs/roadmap_state.json`
- `outputs/phase_status.json`
- `outputs/reports/daily/*.md`
- `outputs/reports/weekly_report.md`
- `outputs/production_readiness_report.json`

## Safety Notes

- Live path is implemented with Binance signed adapter (`/api/v3/order/test` by default).
- Phase progression is gate-driven and blocks on risk/safety failures.

## Production Readiness

```bash
python scripts/create_human_live_approval_template.py
python scripts/approve_human_live_approval.py --by "your_name"
python scripts/bootstrap_compliance_bundle.py
python scripts/finalize_live_readiness.py
python scripts/verify_production_readiness.py
python scripts/run_limited_live_validation.py
python scripts/run_mlops_data_pipeline.py
```

Live mode guard:

- Set `EXECUTION_MODE=live` only after readiness approval.
- Provide `EXCHANGE_API_KEY` and `EXCHANGE_API_SECRET`.
- Create `outputs/live_readiness_approved.flag` after legal/security sign-off.
- For credential deployment automation:
  - `python scripts/deploy_exchange_credentials.py`
  - `powershell -ExecutionPolicy Bypass -File .\scripts\deploy_exchange_credentials.ps1`
- Create `secrets/exchange_credentials.json` from `secrets/exchange_credentials.example.json`.
- Limited live validation passes only when credentials are present and filled ratio is >= 95%.

Autonomous live-readiness worker (keeps retrying until pass):

```bash
python scripts/autonomous_live_readiness_worker.py
```

## Full operational closure (org + exchange + extended compliance)

Bootstrap extended docs and organizational sign-off template:

```bash
python scripts/bootstrap_full_operations.py
```

Lab-only sign-offs (not a legal substitute; for sandbox automation only):

```bash
python scripts/bootstrap_full_operations.py --lab-demo-signoffs
```

Verify Binance credentials with a **read-only** signed `GET /api/v3/account` (no orders):

```bash
python scripts/verify_exchange_credentials.py
```

End-to-end gate (writes `outputs/full_operational_gate_report.json`):

```bash
# Strict production profile (default):
set FULL_OPS_PROFILE=strict
python scripts/verify_full_operational_gate.py
```

Lab profile (sandbox only):

```bash
set FULL_OPS_PROFILE=lab
python scripts/verify_full_operational_gate.py
```

Strict profile (recommended production baseline):

```bash
set FULL_OPS_PROFILE=strict
python scripts/verify_full_operational_gate.py
```

Long-run **paper** stability (no live orders):

```bash
python scripts/run_operational_soak_test.py
```

Policy and limits (human review, not auto-enforced everywhere yet):

- [configs/operational_limits.json](configs/operational_limits.json)
- [configs/human_approval_policy.json](configs/human_approval_policy.json)

Close remaining items in autonomous lab mode (writes waiver + matrix):

```bash
python scripts/close_remaining_items.py
```

Full architecture and operations manual:

- [docs/AutonomousCompany_Complete_Manual.md](docs/AutonomousCompany_Complete_Manual.md)

## Emergency & AIOps

- External kill switch:

```bash
python scripts/trigger_external_kill_switch.py
```

- Optional webhook alerts:
  - set `OPS_ALERT_WEBHOOK_URL` in environment

## Open-Closed-Loop Pilot Agent (sandbox)

Safety constraints are enforced in three layers:

- `sandbox required`: command fails without `--sandbox`
- `human approval gate`: required when `--require-approval` and non-dry-run
- `allowlist only`: executes action IDs from `configs/openclo_pilot_allowlist.json`

Create approval artifact:

```bash
python scripts/create_human_openclo_approval_template.py
python scripts/approve_human_openclo.py --by "your_name"
```

Pilot dry-run:

```bash
python scripts/run_openclo_pilot.py --sandbox --dry-run --goal "게이트 실패 진단"
```

Pilot execution (sandbox + approval gate):

```bash
python scripts/run_openclo_pilot.py --sandbox --require-approval --goal "현재 운영 리스크 보완"
```

## Personal Solo Mode (self-funding)

If you operate with personal funds only (no client assets), external legal/tax
advisor sign-off can be treated as optional for MVP progress in this repository.
Use explicit waiver records and keep evidence logs.

- Recommended closure path for personal solo mode:
  1. `python scripts/close_remaining_items.py`
  2. Check `outputs/full_operational_gate_report.json` -> `ok: true`
  3. Keep `outputs/external_dependency_waivers.json` and `outputs/completion_matrix.md`

## Monitoring Dashboard (browser)

Run local monitoring server:

```bash
python scripts/monitoring_server.py
```

Windows background start:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_monitoring.ps1
```

Open in browser:

- [http://127.0.0.1:8787](http://127.0.0.1:8787)

API endpoint for machine check:

- [http://127.0.0.1:8787/api/status](http://127.0.0.1:8787/api/status)
