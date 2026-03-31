"""Fast loop runtime interface (non-blocking policy read)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np

from src.execution.models import FillEvent
from src.execution.order_router import OrderRouter
from src.interface.policy_buffer import PolicyBuffer
from src.ops.alerts import send_alert
from src.risk.guard import RiskGuard
from src.system1.executor import System1Executor


@dataclass
class FastLoopResult:
    actions: np.ndarray
    strategy_returns: np.ndarray
    position_changes: np.ndarray
    latency_ms: List[float]
    fills: List[FillEvent]


class FastLoopRuntime:
    """Consumes market ticks and never blocks on slow-loop computation."""

    def __init__(
        self,
        executor: System1Executor,
        policy_buffer: PolicyBuffer,
        risk_guard: RiskGuard,
        order_router: OrderRouter,
    ) -> None:
        self.executor = executor
        self.policy_buffer = policy_buffer
        self.risk_guard = risk_guard
        self.order_router = order_router
        
        # Initialize Evaluator Agent for the AI Cross-Check Pipeline
        from src.agentic.evaluator_agent import EvaluatorAgent
        self.evaluator = EvaluatorAgent()

    def run(self, ticks: Iterable[np.ndarray], returns: np.ndarray) -> FastLoopResult:
        ticks_arr = np.asarray(list(ticks), dtype=np.float32)
        actions = np.zeros(len(ticks_arr), dtype=np.int64)
        strat = np.zeros(len(ticks_arr), dtype=np.float32)
        latency_ms: List[float] = []
        fills: List[FillEvent] = []

        day_pnl = 0.0
        week_window = 200
        kill_alert_sent = False
        for i, row in enumerate(ticks_arr):
            t0 = time.perf_counter()
            gamma, beta = self.policy_buffer.read()
            _, action = self.executor.infer(row, gamma, beta)
            elapsed = (time.perf_counter() - t0) * 1000.0
            latency_ms.append(elapsed)
            self.policy_buffer.tick_interpolate()

            volatility = float(abs(row[1])) if row.shape[0] > 1 else 0.0
            start_w = max(0, i - week_window)
            week_pnl = float(np.sum(strat[start_w:i])) if i > 0 else 0.0
            safe_action = self.risk_guard.evaluate(
                action=action,
                realized_pnl=float(strat[i - 1]) if i > 0 else 0.0,
                day_pnl=day_pnl,
                volatility=volatility,
                week_pnl=week_pnl,
            )

            # AI Evaluator Pipeline (Cross-Check)
            # Only trigger LLM evaluation for actual trades (not holds) to save latency and tokens
            ai_approved = True
            reason_code = "fast_loop_signal"
            
            if safe_action != 1:  # If RiskGuard didn't block it and it's a Buy/Sell
                proposal = {
                    "action": int(safe_action),
                    "symbol": self.order_router.config.symbol,
                    "signal_strength": float(action)
                }
                portfolio_state = {
                    "realized_pnl": float(strat[i - 1]) if i > 0 else 0.0,
                    "day_pnl": day_pnl,
                    "current_position": float(safe_action - 1)
                }
                market_context = {
                    "volatility": volatility
                }
                
                eval_res = self.evaluator.evaluate_trade(proposal, portfolio_state, market_context)
                if not eval_res["approved"]:
                    safe_action = 1  # Force Hold
                    ai_approved = False
                    reason_code = f"ai_evaluator_rejected: {eval_res['reason']}"
                else:
                    reason_code = f"ai_evaluator_approved: {eval_res['reason']}"

            actions[i] = safe_action
            position = float(safe_action - 1)  # sell=-1, hold=0, buy=+1
            strat[i] = position * float(returns[i])
            day_pnl += float(strat[i])
            
            # Fill logic
            fill = self.order_router.submit_action(
                action=safe_action,
                price_hint=max(0.0001, 100.0 + float(i) + float(row[0]) * 100.0),
                decision_id=f"dec_{i:08d}",
                reason_code=reason_code,
                risk_approved=(safe_action == action) and ai_approved,
                feature_row=row.astype(float).tolist(),
            )
            if fill is not None:
                fills.append(fill)
            if self.risk_guard.kill_switch and not kill_alert_sent:
                send_alert(
                    "risk_kill_switch_triggered",
                    {"reason": self.risk_guard.last_reason, "tick_index": i, "day_pnl": day_pnl},
                )
                kill_alert_sent = True

        position_changes = np.diff(actions.astype(np.float32), prepend=actions[0])
        return FastLoopResult(
            actions=actions,
            strategy_returns=strat,
            position_changes=position_changes,
            latency_ms=latency_ms,
            fills=fills,
        )
