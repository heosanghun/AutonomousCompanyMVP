"""Lock-free-ish policy buffer for fast/slow loop handoff."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class BufferState:
    gamma: np.ndarray
    beta: np.ndarray


class PolicyBuffer:
    """Double-slot buffer with atomic swap + optional interpolation."""

    def __init__(
        self,
        clip: float = 5.0,
        interpolate: bool = True,
        interpolation_steps: int = 5,
        hysteresis_forward: float = 0.3,
    ) -> None:
        self.clip = clip
        self.interpolate = interpolate
        self.interpolation_steps = max(1, interpolation_steps)
        self.hysteresis_forward = hysteresis_forward
        init = BufferState(
            gamma=np.array(1.0, dtype=np.float32),
            beta=np.array(0.0, dtype=np.float32),
        )
        self._active = init
        self._standby = init
        self._lock = threading.Lock()
        self._interpolation_step = self.interpolation_steps
        self._from = init
        self._to = init

    def read(self) -> Tuple[np.ndarray, np.ndarray]:
        """Fast loop read-only path."""
        with self._lock:
            return self._active.gamma.copy(), self._active.beta.copy()

    def write(self, gamma: np.ndarray, beta: np.ndarray) -> bool:
        """Slow loop write path; returns True if accepted."""
        g = np.clip(np.asarray(gamma, dtype=np.float32).ravel(), -self.clip, self.clip)
        b = np.clip(np.asarray(beta, dtype=np.float32).ravel(), -self.clip, self.clip)
        with self._lock:
            diff_g = np.abs(g - self._active.gamma).max()
            diff_b = np.abs(b - self._active.beta).max()
            if diff_g < self.hysteresis_forward and diff_b < self.hysteresis_forward:
                return False

            self._standby = BufferState(gamma=g, beta=b)
            if self.interpolate and self.interpolation_steps > 1:
                self._from = BufferState(
                    gamma=self._active.gamma.copy(),
                    beta=self._active.beta.copy(),
                )
                self._to = BufferState(gamma=g.copy(), beta=b.copy())
                self._interpolation_step = 0
                self._active = BufferState(
                    gamma=self._from.gamma.copy(),
                    beta=self._from.beta.copy(),
                )
            else:
                self._active, self._standby = self._standby, self._active
                self._interpolation_step = self.interpolation_steps
            return True

    def tick_interpolate(self) -> None:
        """Advance interpolation by one step from fast loop."""
        with self._lock:
            if self._interpolation_step >= self.interpolation_steps:
                return
            self._interpolation_step += 1
            alpha = self._interpolation_step / float(self.interpolation_steps)
            self._active = BufferState(
                gamma=((1.0 - alpha) * self._from.gamma + alpha * self._to.gamma).astype(
                    np.float32
                ),
                beta=((1.0 - alpha) * self._from.beta + alpha * self._to.beta).astype(
                    np.float32
                ),
            )
