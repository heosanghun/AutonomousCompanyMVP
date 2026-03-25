"""Drift detection: mean/vol shift, PSI, and Kolmogorov–Smirnov-style statistic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass
class DriftConfig:
    mean_shift_threshold: float = 0.0015
    vol_shift_threshold: float = 0.02
    psi_threshold: float = 0.2
    ks_threshold: float = 0.15


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
            "psi": 0.0,
            "ks_stat": 0.0,
        }

    mean_shift = float(abs(np.mean(r) - np.mean(b)))
    vol_shift = float(abs(np.std(r) - np.std(b)))
    drift = mean_shift >= config.mean_shift_threshold or vol_shift >= config.vol_shift_threshold
    psi = population_stability_index(b, r, n_bins=10)
    ks_stat = two_sample_ks_statistic(b, r)
    drift = drift or psi >= config.psi_threshold or ks_stat >= config.ks_threshold
    return {
        "drift_detected": drift,
        "mean_shift": mean_shift,
        "vol_shift": vol_shift,
        "psi": psi,
        "ks_stat": ks_stat,
    }


def population_stability_index(expected: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    """
    Histogram-based PSI for distribution shift (lower is more stable).
    """
    e = np.asarray(expected, dtype=np.float64).ravel()
    a = np.asarray(actual, dtype=np.float64).ravel()
    if len(e) < 2 or len(a) < 2:
        return 0.0
    qs = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.unique(np.quantile(e, qs))
    if len(edges) < 2:
        edges = np.array([float(np.min(e)), float(np.max(e)) + 1e-12])
    hist_e, _ = np.histogram(e, bins=edges)
    hist_a, _ = np.histogram(a, bins=edges)
    pe = hist_e / max(len(e), 1)
    pa = hist_a / max(len(a), 1)
    pe = np.clip(pe, 1e-6, 1.0)
    pa = np.clip(pa, 1e-6, 1.0)
    return float(np.sum((pa - pe) * np.log(pa / pe)))


def two_sample_ks_statistic(x: np.ndarray, y: np.ndarray) -> float:
    """Simple two-sample KS statistic D = sup |F_x - F_y| (0..1)."""
    a = np.sort(np.asarray(x, dtype=np.float64).ravel())
    b = np.sort(np.asarray(y, dtype=np.float64).ravel())
    if len(a) < 1 or len(b) < 1:
        return 0.0
    vals = np.unique(np.concatenate([a, b]))
    if len(vals) == 0:
        return 0.0
    i = j = 0
    fa = fb = 0.0
    na, nb = len(a), len(b)
    best = 0.0
    for v in vals:
        while i < na and a[i] <= v:
            i += 1
        while j < nb and b[j] <= v:
            j += 1
        fa = i / na
        fb = j / nb
        best = max(best, abs(fa - fb))
    return float(best)
