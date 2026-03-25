"""MVP entrypoint for async autonomous trading simulation."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from src.audit.logger import AuditLogger
from src.bootstrap_env import load_dotenv_files
from src.execution.broker import LiveBrokerEnvGuard, LiveBrokerStub, PaperBroker
from src.execution.order_router import OrderRouter, RouterConfig
from src.interface.policy_buffer import PolicyBuffer
from src.ops.drift_guard import DriftConfig, detect_return_drift
from src.risk.guard import RiskConfig, RiskGuard
from src.runtime.engine import AsyncTradingEngine
from src.system1.executor import System1Config, System1Executor
from src.system1.runtime import FastLoopRuntime
from src.system2.planner import System2Config, System2Planner

load_dotenv_files()


def _load_runtime_config() -> dict:
    cfg_path = Path("configs/runtime.json")
    if not cfg_path.exists():
        return {
            "execution_mode": "paper",
            "symbol": "BTCUSDT",
            "default_qty": 1.0,
            "paper_slippage_bps": 2.0,
            "live_guard": {
                "require_readiness_file": True,
                "readiness_file": "outputs/live_readiness_approved.flag",
                "fills_file": "outputs/live_fills.jsonl",
                "test_order": True,
            },
        }
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def generate_mock_data(n: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    # Slightly positive drift keeps baseline validation deterministic.
    ret = (rng.standard_normal(n) * 0.002 + 0.00035).astype(np.float32)
    vol = np.abs(rng.standard_normal(n) * 0.02).astype(np.float32)
    micro = (rng.standard_normal(n) * 0.5).astype(np.float32)
    ticks = np.column_stack([ret, vol, micro]).astype(np.float32)
    return ticks, ret


def run(output_dir: str = "outputs") -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    audit = AuditLogger(out / "audit.log")

    policy_buffer = PolicyBuffer()
    risk_guard = RiskGuard(RiskConfig())
    runtime_cfg = _load_runtime_config()
    mode = os.environ.get("EXECUTION_MODE", runtime_cfg.get("execution_mode", "paper")).lower()
    symbol = runtime_cfg.get("symbol", "BTCUSDT")
    qty = float(runtime_cfg.get("default_qty", 1.0))
    paper_slippage = float(runtime_cfg.get("paper_slippage_bps", 2.0))
    live_guard_cfg = runtime_cfg.get("live_guard", {})
    readiness_file = live_guard_cfg.get("readiness_file", "outputs/live_readiness_approved.flag")
    live_fills_file = live_guard_cfg.get("fills_file", "outputs/live_fills.jsonl")
    live_test_order = bool(live_guard_cfg.get("test_order", True))

    if mode == "paper":
        broker = PaperBroker(out / "fills.jsonl", slippage_bps=paper_slippage)
    elif mode == "live":
        broker = LiveBrokerEnvGuard(
            readiness_flag_path=readiness_file,
            fills_path=live_fills_file,
            test_order=live_test_order,
        )
    else:
        broker = LiveBrokerStub()
    router = OrderRouter(broker, RouterConfig(mode=mode, symbol=symbol, default_qty=qty))
    system1 = System1Executor(System1Config())
    fast = FastLoopRuntime(system1, policy_buffer, risk_guard, router)
    planner = System2Planner(System2Config(), policy_buffer)
    engine = AsyncTradingEngine(fast, planner)

    ticks, returns = generate_mock_data()
    baseline = returns[:500]
    recent = returns[-200:]
    drift_info = detect_return_drift(baseline, recent, DriftConfig())
    audit.log("startup", {"n_ticks": len(ticks)})
    result = engine.run(ticks=ticks, returns=returns)
    audit.log(
        "completed",
        {
            "metrics": result.metrics,
            "n_updates": result.n_updates,
            "n_interrupts": result.n_interrupts,
            "n_fills": result.n_fills,
            "kill_switch": risk_guard.kill_switch,
            "execution_mode": mode,
            "drift": drift_info,
        },
    )

    payload = {
        "metrics": result.metrics,
        "n_updates": result.n_updates,
        "n_interrupts": result.n_interrupts,
        "n_fills": result.n_fills,
        "kill_switch": risk_guard.kill_switch,
        "execution_mode": mode,
        "drift": drift_info,
    }
    with (out / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=True, indent=2))
