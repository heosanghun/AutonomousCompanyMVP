"""FiLM bridge: convert regime vector z to (gamma, beta)."""

from __future__ import annotations

import numpy as np


class FiLMGenerator:
    """Small numpy-based FiLM generator for MVP runtime."""

    def __init__(self, z_dim: int = 32, num_channels: int = 64, clip: float = 5.0) -> None:
        self.z_dim = z_dim
        self.num_channels = num_channels
        self.clip = clip
        rng = np.random.default_rng(42)
        self.w_gamma = (rng.standard_normal((z_dim, num_channels)) * 0.1).astype(np.float32)
        self.w_beta = (rng.standard_normal((z_dim, num_channels)) * 0.1).astype(np.float32)

    def __call__(self, z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        z = np.asarray(z, dtype=np.float32).reshape(-1, self.z_dim)
        gamma = np.tanh(z @ self.w_gamma) * self.clip
        beta = np.tanh(z @ self.w_beta) * self.clip
        return gamma.squeeze(0), beta.squeeze(0)


def apply_film(x: np.ndarray, gamma: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """Feature-wise affine modulation."""
    return np.asarray(gamma, dtype=np.float32) * np.asarray(x, dtype=np.float32) + np.asarray(
        beta, dtype=np.float32
    )
