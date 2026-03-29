"""Generate System2 policy proposal and run sandbox simulation validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agentic.policy_agent import propose_system2_policy
from src.data.market_data import generate_mock_data
from src.interface.policy_buffer import PolicyBuffer
from src.runtime.engine import AsyncTradingEngine
from src.system1.executor import System1Config, System1Executor
from src.system1.runtime import FastLoopRuntime
from src.system2.planner import System2Config, System2Planner
from src.execution.broker import PaperBroker
from src.execution.order_router import OrderRouter, RouterConfig
from src.risk.guard import RiskConfig, RiskGuard


def run_sandbox(policy: dict) -> dict:
    ticks, returns = generate_mock_data(n=800, seed=7)
    broker = PaperBroker("outputs/policy_sandbox/fills.jsonl", slippage_bps=2.0, run_id="policy_sandbox")
    router = OrderRouter(broker, RouterConfig(mode="paper", symbol="BTCUSDT", default_qty=1.0))
    system1 = System1Executor(System1Config())
    buffer = PolicyBuffer()
    risk = RiskGuard(RiskConfig(max_daily_loss=0.03, max_weekly_loss=0.05, max_position_abs=1.0))
    planner = System2Planner(
        System2Config(
            slow_interval_steps=int(policy["slow_interval_steps"]),
            force_trigger_volatility=float(policy["force_trigger_volatility"]),
            force_trigger_imbalance=float(policy["force_trigger_imbalance"]),
        ),
        buffer,
    )
    fast = FastLoopRuntime(system1, buffer, risk, router)
    engine = AsyncTradingEngine(fast, planner)
    res = engine.run(ticks=ticks, returns=returns)
    metrics = res.metrics
    passed = bool(metrics.get("latency_p99_ms", 999.0) <= 10.0 and metrics.get("mdd", 1.0) <= 0.2)
    return {
        "passed": passed,
        "metrics": metrics,
        "n_updates": res.n_updates,
        "n_fills": res.n_fills,
        "criteria": {"latency_p99_ms_le": 10.0, "mdd_le": 0.2},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status-path", default="outputs/summary.json")
    parser.add_argument("--out", default="outputs/policy/system2_policy_proposal.json")
    args = parser.parse_args()

    summary_path = Path(args.status_path)
    status = {}
    if summary_path.exists():
        try:
            status = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            status = {}
    latency = float((status.get("metrics", {}) or {}).get("latency_p99_ms") or 0.0)
    drift = bool((status.get("drift", {}) or {}).get("drift_detected", False))
    proposal = propose_system2_policy(latency_p99_ms=latency, drift_detected=drift)
    sandbox = run_sandbox(proposal)

    from src.agentic.cross_verify import cross_verify_decision
    cross_verification = cross_verify_decision(
        proposal={"policy_update": proposal, "sandbox_metrics": sandbox},
        review_scope="system2_policy_update",
    )

    payload = {
        "mode": "proposal_only",
        "input": {"latency_p99_ms": latency, "drift_detected": drift},
        "proposal": proposal,
        "sandbox_validation": sandbox,
        "cross_verification": cross_verification,
        "requires_human_approval": True,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if sandbox.get("passed", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())

