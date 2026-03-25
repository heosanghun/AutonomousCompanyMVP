"""Minimal MLOps data pipeline: ingest -> quality -> features -> registry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class DataQualityConfig:
    max_missing_ratio: float = 0.001
    max_abs_return: float = 0.2


def ingest_csv(path: str | Path) -> np.ndarray:
    arr = np.genfromtxt(path, delimiter=",", names=True, dtype=np.float32)
    return np.column_stack([arr[name] for name in arr.dtype.names]).astype(np.float32)


def validate_quality(data: np.ndarray, cfg: DataQualityConfig) -> dict:
    if data.size == 0:
        return {"ok": False, "reason": "empty_dataset"}
    missing_ratio = float(np.isnan(data).mean())
    max_abs = float(np.nanmax(np.abs(data[:, 0])))
    ok = missing_ratio <= cfg.max_missing_ratio and max_abs <= cfg.max_abs_return
    return {"ok": ok, "missing_ratio": missing_ratio, "max_abs_return": max_abs}


def build_features(data: np.ndarray) -> np.ndarray:
    ret = data[:, 0]
    vol = np.abs(ret)
    ma5 = np.convolve(ret, np.ones(5) / 5.0, mode="same")
    return np.column_stack([ret, vol, ma5]).astype(np.float32)


def register_snapshot(features: np.ndarray, out_dir: str | Path, dataset_name: str) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = features.tobytes()
    digest = hashlib.sha256(raw).hexdigest()
    npy_path = out / f"{dataset_name}_{digest[:12]}.npy"
    np.save(npy_path, features)
    meta = {
        "dataset_name": dataset_name,
        "hash": digest,
        "shape": list(features.shape),
        "artifact": str(npy_path),
    }
    (out / f"{dataset_name}_{digest[:12]}.json").write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")
    return meta
