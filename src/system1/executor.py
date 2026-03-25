"""System1 executor: low-latency action inference."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.interface.film import apply_film


@dataclass
class System1Config:
    lookback: int = 60
    feature_dim: int = 64
    action_dim: int = 3  # sell / hold / buy


class System1Executor:
    """Simple MVP executor that mimics fast-path inference behavior."""

    def __init__(self, config: System1Config) -> None:
        self.config = config
        rng = np.random.default_rng(7)
        self.w_in = (rng.standard_normal((3, config.feature_dim)) * 0.1).astype(np.float32)
        self.w_out = (rng.standard_normal((config.feature_dim, config.action_dim)) * 0.1).astype(
            np.float32
        )

    def _encode(self, tick_row: np.ndarray) -> np.ndarray:
        x = np.asarray(tick_row, dtype=np.float32).reshape(1, -1)  # [ret, vol, micro]
        return np.tanh(x @ self.w_in).squeeze(0)

    def infer(self, tick_row: np.ndarray, gamma: np.ndarray, beta: np.ndarray) -> tuple[np.ndarray, int]:
        features = self._encode(tick_row)
        modulated = apply_film(features, gamma, beta)
        logits = np.asarray(modulated @ self.w_out, dtype=np.float32)
        action = int(np.argmax(logits))
        return logits, action
