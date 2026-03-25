"""Runtime risk controls for autonomous trading."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskConfig:
    max_daily_loss: float = 0.03
    max_position_abs: float = 1.0
    max_consecutive_errors: int = 3
    hard_volatility_breaker: float = 0.08


class RiskGuard:
    """Enforces position and loss constraints with kill-switch support."""

    def __init__(self, config: RiskConfig) -> None:
        self.config = config
        self.kill_switch = False
        self.consecutive_errors = 0

    def on_error(self) -> None:
        self.consecutive_errors += 1
        if self.consecutive_errors >= self.config.max_consecutive_errors:
            self.kill_switch = True

    def reset_error_streak(self) -> None:
        self.consecutive_errors = 0

    def evaluate(self, action: int, realized_pnl: float, day_pnl: float, volatility: float) -> int:
        """
        Returns safe action:
        0 sell, 1 hold, 2 buy.
        """
        if self.kill_switch:
            return 1
        if day_pnl <= -abs(self.config.max_daily_loss):
            self.kill_switch = True
            return 1
        if abs(volatility) >= self.config.hard_volatility_breaker:
            return 1

        target_pos = float(action - 1)
        if abs(target_pos) > self.config.max_position_abs:
            return 1

        if realized_pnl < -abs(self.config.max_daily_loss) * 0.5 and action == 2:
            return 1
        return action
