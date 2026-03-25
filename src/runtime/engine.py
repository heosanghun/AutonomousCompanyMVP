"""Asynchronous multi-scale engine wiring system2 -> film -> buffer -> system1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from src.eval.metrics import compute_all, latency_stats
from src.system1.runtime import FastLoopRuntime
from src.system2.planner import System2Planner


@dataclass
class EngineResult:
    metrics: Dict[str, float]
    n_updates: int
    n_interrupts: int
    n_fills: int


class AsyncTradingEngine:
    """Coordinates slow-loop updates and fast-loop execution."""

    def __init__(self, fast_runtime: FastLoopRuntime, planner: System2Planner) -> None:
        self.fast_runtime = fast_runtime
        self.planner = planner

    def run(self, ticks: np.ndarray, returns: np.ndarray) -> EngineResult:
        updates = 0
        interrupts = 0
        micro = ticks[:, 2] if ticks.ndim == 2 and ticks.shape[1] >= 3 else np.zeros(len(ticks))

        for i in range(1, len(returns) + 1):
            start = max(0, i - 60)
            win_ret = returns[start:i]
            win_micro = micro[start:i]
            vol = float(np.std(win_ret)) if len(win_ret) > 0 else 0.0
            imb = float(np.mean(win_micro)) if len(win_micro) > 0 else 0.0
            force = (
                abs(vol) >= self.planner.config.force_trigger_volatility
                or abs(imb) >= self.planner.config.force_trigger_imbalance
            )
            if force:
                interrupts += 1
            if self.planner.maybe_update(i, win_ret, win_micro, force_trigger=force):
                updates += 1

        fast_res = self.fast_runtime.run(ticks=ticks, returns=returns)
        m = compute_all(fast_res.strategy_returns)
        m.update(latency_stats(fast_res.latency_ms))
        return EngineResult(
            metrics=m,
            n_updates=updates,
            n_interrupts=interrupts,
            n_fills=len(fast_res.fills),
        )
