"""MVP entrypoint for async autonomous trading simulation."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import numpy as np

from src.audit.logger import AuditLogger
from src.bootstrap_env import load_dotenv_files
from src.data.market_data import (
    fetch_binance_klines,
    generate_mock_data,
    ws_prices_to_ticks_returns,
)
from src.data.ws_mini_ticker import fetch_binance_ws_mini_ticker_prices
from src.execution.broker import LiveBrokerEnvGuard, LiveBrokerStub, PaperBroker
from src.execution.order_router import OrderRouter, RouterConfig
from src.interface.policy_buffer import PolicyBuffer
from src.ops.alerts import send_alert
from src.ops.drift_guard import DriftConfig, detect_return_drift
from src.mlops.experiment_log import append_experiment
from src.ops.reconcile import reconcile_counts
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
            "data_source": "mock",
            "mock_ticks": 1000,
            "live_guard": {
                "require_readiness_file": True,
                "readiness_file": "outputs/live_readiness_approved.flag",
                "fills_file": "outputs/live_fills.jsonl",
                "per_run_fills": True,
                "test_order": True,
            },
        }
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def _load_operational_limits() -> dict:
    p = Path("configs/operational_limits.json")
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_ticks_returns(runtime_cfg: dict, symbol: str) -> tuple[np.ndarray, np.ndarray]:
    src = os.environ.get("MARKET_DATA_SOURCE", runtime_cfg.get("data_source", "mock")).lower()
    n = int(runtime_cfg.get("mock_ticks", 1000))
    seed = int(runtime_cfg.get("mock_seed", 0))
    if src == "binance_rest":
        try:
            interval = str(runtime_cfg.get("klines_interval", "1m"))
            limit = int(runtime_cfg.get("klines_limit", 1000))
            base = str(runtime_cfg.get("binance_rest_base", "https://api.binance.com"))
            return fetch_binance_klines(symbol, interval=interval, limit=limit, base_url=base)
        except Exception as e:
            send_alert("market_data_fallback_mock", {"error": str(e), "symbol": symbol})
            return generate_mock_data(n=n, seed=seed)
    if src == "binance_ws":
        try:
            ws_n = int(runtime_cfg.get("ws_price_samples", n))
            timeout = float(runtime_cfg.get("ws_per_message_timeout_sec", 15.0))
            prices = fetch_binance_ws_mini_ticker_prices(
                symbol,
                max(ws_n, 2),
                per_message_timeout_sec=timeout,
            )
            return ws_prices_to_ticks_returns(prices)
        except Exception as e:
            send_alert("market_data_ws_fallback_mock", {"error": str(e), "symbol": symbol})
            return generate_mock_data(n=n, seed=seed)
    return generate_mock_data(n=n, seed=seed)


def run(output_dir: str = "outputs") -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    runtime_cfg_pre = _load_runtime_config()
    mode_pre = os.environ.get("EXECUTION_MODE", runtime_cfg_pre.get("execution_mode", "paper")).lower()
    if mode_pre == "paper" and bool(runtime_cfg_pre.get("fresh_fills_per_run", True)):
        for name in ("fills.jsonl", "live_fills.jsonl"):
            fp = out / name
            if fp.exists():
                fp.unlink()
    audit = AuditLogger(out / "audit.log")
    run_id = str(uuid.uuid4())

    policy_buffer = PolicyBuffer()
    limits = _load_operational_limits()
    max_daily_loss = float(limits.get("max_daily_loss_pct_equity", 0.02))
    max_weekly_loss = float(limits.get("max_weekly_loss_pct_equity", 0.05))
    max_pos = float(limits.get("max_leverage", 1.0))
    max_notional_order = float(limits.get("max_notional_usd_per_order", 0.0) or 0.0)
    max_open_notional = float(limits.get("max_open_notional_usd", 0.0) or 0.0)
    risk_guard = RiskGuard(
        RiskConfig(
            max_daily_loss=max_daily_loss,
            max_weekly_loss=max_weekly_loss,
            max_position_abs=max_pos,
        )
    )
    runtime_cfg = _load_runtime_config()
    mode = os.environ.get("EXECUTION_MODE", runtime_cfg.get("execution_mode", "paper")).lower()
    symbol = runtime_cfg.get("symbol", "BTCUSDT")
    qty = float(runtime_cfg.get("default_qty", 1.0))
    paper_slippage = float(runtime_cfg.get("paper_slippage_bps", 2.0))
    market_impact = float(runtime_cfg.get("market_impact_factor", 0.5))
    live_guard_cfg = runtime_cfg.get("live_guard", {})
    readiness_file = live_guard_cfg.get("readiness_file", "outputs/live_readiness_approved.flag")
    live_test_order = bool(live_guard_cfg.get("test_order", True))
    per_run_fills = bool(live_guard_cfg.get("per_run_fills", True))
    if per_run_fills:
        live_fills_path = out / "live_fills.jsonl"
    else:
        live_fills_path = Path(live_guard_cfg.get("fills_file", "outputs/live_fills.jsonl"))

    if mode == "paper":
        broker = PaperBroker(out / "fills.jsonl", slippage_bps=paper_slippage, market_impact_factor=market_impact, run_id=run_id)
    elif mode == "live":
        broker = LiveBrokerEnvGuard(
            readiness_flag_path=readiness_file,
            fills_path=live_fills_path,
            test_order=live_test_order,
            run_id=run_id,
        )
    else:
        broker = LiveBrokerStub()
    router = OrderRouter(
        broker,
        RouterConfig(
            mode=mode,
            symbol=symbol,
            default_qty=qty,
            max_notional_usd_per_order=max_notional_order,
            max_open_notional_usd=max_open_notional,
        ),
    )
    system1 = System1Executor(System1Config())
    fast = FastLoopRuntime(system1, policy_buffer, risk_guard, router)
    planner = System2Planner(System2Config(), policy_buffer)
    engine = AsyncTradingEngine(fast, planner)

    ticks, returns = _load_ticks_returns(runtime_cfg, symbol)
    baseline = returns[:500] if len(returns) >= 500 else returns
    recent = returns[-200:] if len(returns) >= 200 else returns
    drift_info = detect_return_drift(baseline, recent, DriftConfig())
    if drift_info.get("drift_detected"):
        send_alert("drift_detected", drift_info)
    ext_ks = out / "external_kill_switch.flag"
    if ext_ks.exists():
        risk_guard.trigger_external_kill_switch("external_kill_switch.flag")
        send_alert("external_kill_switch", {"path": str(ext_ks)})
    audit.log("startup", {"n_ticks": len(ticks), "symbol": symbol, "data_source": runtime_cfg.get("data_source", "mock")})
    
    from src.ops.auto_healer import AutoHealer
    import logging
    healer = AutoHealer(logger=logging.getLogger("MainRuntime"))
    
    try:
        result = healer.run_with_healing(engine.run, ticks=ticks, returns=returns)
    except Exception as e:
        audit.log("system_crash", {"error": str(e), "action": "abort_run"})
        raise e
        
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
        "run_id": run_id,
        "metrics": result.metrics,
        "n_updates": result.n_updates,
        "n_interrupts": result.n_interrupts,
        "n_fills": result.n_fills,
        "kill_switch": risk_guard.kill_switch,
        "execution_mode": mode,
        "drift": drift_info,
        "risk_reason": risk_guard.last_reason,
    }
    with (out / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
    payload["reconcile"] = reconcile_counts(out)
    append_experiment(
        "main_runtime",
        {
            "metrics": result.metrics,
            "n_fills": result.n_fills,
            "kill_switch": risk_guard.kill_switch,
            "reconcile_ok": payload["reconcile"].get("ok"),
        },
        run_id=run_id,
        out_dir=out / "mlops",
    )

    cancel_flag = os.environ.get("CANCEL_OPEN_ORDERS_ON_KILL_SWITCH", "").lower() in ("1", "true", "yes")
    if cancel_flag and risk_guard.kill_switch and mode == "live":
        from src.execution.binance_emergency import cancel_all_open_orders

        cancel_res = cancel_all_open_orders(symbol=symbol)
        payload["exchange_cancel_on_kill"] = cancel_res
        audit.log("exchange_cancel_on_kill", cancel_res)

    with (out / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=True, indent=2))
