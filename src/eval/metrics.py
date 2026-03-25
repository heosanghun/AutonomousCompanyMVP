"""Risk-centric evaluation metrics for automated trading."""

from __future__ import annotations

from typing import Dict, Iterable

import numpy as np


def cagr(returns: np.ndarray, periods_per_year: float = 252.0) -> float:
    if len(returns) == 0:
        return 0.0
    total = np.prod(1.0 + returns)
    years = len(returns) / periods_per_year
    if years <= 0:
        return 0.0
    return float(total ** (1.0 / years) - 1.0)


def annualized_vol(returns: np.ndarray, periods_per_year: float = 252.0) -> float:
    if len(returns) < 2:
        return 0.0
    return float(np.std(returns) * np.sqrt(periods_per_year))


def sharpe(returns: np.ndarray, periods_per_year: float = 252.0, risk_free: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    excess = np.mean(returns) - risk_free / periods_per_year
    sigma = np.std(returns)
    if sigma < 1e-10:
        return 0.0
    return float(excess / sigma * np.sqrt(periods_per_year))


def sortino(
    returns: np.ndarray,
    periods_per_year: float = 252.0,
    risk_free: float = 0.0,
) -> float:
    if len(returns) < 2:
        return 0.0
    excess = np.mean(returns) - risk_free / periods_per_year
    downside = returns[returns < 0]
    if len(downside) == 0:
        return 10.0
    sigma_d = np.std(downside)
    if sigma_d < 1e-10:
        return 0.0
    return float(excess / sigma_d * np.sqrt(periods_per_year))


def max_drawdown(returns: np.ndarray) -> float:
    if len(returns) == 0:
        return 0.0
    equity = np.cumprod(1.0 + returns)
    peak = np.maximum.accumulate(equity)
    dd = (peak - equity) / (peak + 1e-10)
    return float(np.max(dd))


def win_rate(returns: np.ndarray) -> float:
    if len(returns) == 0:
        return 0.0
    return float(np.mean(returns > 0))


def profit_factor(returns: np.ndarray) -> float:
    gains = returns[returns > 0].sum()
    losses = np.abs(returns[returns < 0].sum())
    if losses < 1e-10:
        return 10.0
    return float(gains / losses)


def latency_stats(samples_ms: Iterable[float]) -> Dict[str, float]:
    arr = np.asarray(list(samples_ms), dtype=np.float64)
    if len(arr) == 0:
        return {
            "latency_mean_ms": 0.0,
            "latency_p95_ms": 0.0,
            "latency_p99_ms": 0.0,
        }
    return {
        "latency_mean_ms": float(np.mean(arr)),
        "latency_p95_ms": float(np.percentile(arr, 95)),
        "latency_p99_ms": float(np.percentile(arr, 99)),
    }


def apply_slippage(returns: np.ndarray, position_changes: np.ndarray, bps: float) -> np.ndarray:
    cost = np.abs(position_changes) * (bps / 10000.0)
    return returns - cost


def compute_all(returns: np.ndarray, periods_per_year: float = 252.0) -> Dict[str, float]:
    return {
        "cagr": cagr(returns, periods_per_year),
        "vol_ann": annualized_vol(returns, periods_per_year),
        "sharpe": sharpe(returns, periods_per_year),
        "sortino": sortino(returns, periods_per_year),
        "mdd": max_drawdown(returns),
        "win_rate": win_rate(returns),
        "profit_factor": profit_factor(returns),
        "cum_return": float(np.prod(1.0 + returns) - 1.0) if len(returns) else 0.0,
    }
