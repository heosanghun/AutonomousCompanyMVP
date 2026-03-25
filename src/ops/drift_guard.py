"""Lightweight drift guard for autonomous runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass
class DriftConfig:
    mean_shift_threshold: float = 0.0015
    vol_shift_threshold: float = 0.02


def detect_return_drift(
    baseline_returns: np.ndarray,
    recent_returns: np.ndarray,
    config: DriftConfig,
) -> Dict[str, float | bool]:
    b = np.asarray(baseline_returns, dtype=np.float64)
    r = np.asarray(recent_returns, dtype=np.float64)
    if len(b) < 2 or len(r) < 2:
        return {
            "drift_detected": False,
            "mean_shift": 0.0,
            "vol_shift": 0.0,
        }

    mean_shift = float(abs(np.mean(r) - np.mean(b)))
    vol_shift = float(abs(np.std(r) - np.std(b)))
    drift = mean_shift >= config.mean_shift_threshold or vol_shift >= config.vol_shift_threshold
    return {
        "drift_detected": drift,
        "mean_shift": mean_shift,
        "vol_shift": vol_shift,
    }
