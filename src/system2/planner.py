"""System2 planner: regime inference and FiLM parameter generation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.interface.film import FiLMGenerator
from src.interface.policy_buffer import PolicyBuffer


@dataclass
class System2Config:
    z_dim: int = 32
    feature_dim: int = 64
    slow_interval_steps: int = 40
    force_trigger_volatility: float = 0.03
    force_trigger_imbalance: float = 0.30


class System2Planner:
    """Generates compressed regime vector and updates policy buffer."""

    def __init__(self, config: System2Config, policy_buffer: PolicyBuffer) -> None:
        self.config = config
        self.policy_buffer = policy_buffer
        self.film_gen = FiLMGenerator(
            z_dim=config.z_dim,
            num_channels=config.feature_dim,
            clip=5.0,
        )

    def build_regime_vector(self, window_returns: np.ndarray, window_micro: np.ndarray) -> np.ndarray:
        vol = float(np.std(window_returns)) if len(window_returns) else 0.0
        mom = float(np.mean(window_returns)) if len(window_returns) else 0.0
        imb = float(np.mean(window_micro)) if len(window_micro) else 0.0
        drawdown_proxy = float(np.min(np.cumsum(window_returns))) if len(window_returns) else 0.0
        base = np.array([vol, mom, imb, drawdown_proxy], dtype=np.float32)
        z = np.zeros(self.config.z_dim, dtype=np.float32)
        repeat = min(len(base), self.config.z_dim)
        z[:repeat] = base[:repeat]
        if self.config.z_dim > repeat:
            z[repeat:] = np.tanh(np.linspace(-1, 1, self.config.z_dim - repeat)).astype(np.float32)
        return z

    def maybe_update(
        self,
        step: int,
        window_returns: np.ndarray,
        window_micro: np.ndarray,
        force_trigger: bool = False,
    ) -> bool:
        if step % self.config.slow_interval_steps != 0 and not force_trigger:
            return False
        z = self.build_regime_vector(window_returns, window_micro)
        gamma, beta = self.film_gen(z)
        return self.policy_buffer.write(gamma, beta)
