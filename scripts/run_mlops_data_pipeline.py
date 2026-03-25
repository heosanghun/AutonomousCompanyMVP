"""Run minimal MLOps data pipeline and write quality/registry artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.mlops.data_pipeline import DataQualityConfig, build_features, register_snapshot, validate_quality
from src.mlops.experiment_log import append_experiment


def _generate_dataset(n: int = 2000) -> np.ndarray:
    rng = np.random.default_rng(42)
    ret = (rng.standard_normal(n) * 0.002 + 0.0002).astype(np.float32)
    return ret.reshape(-1, 1)


def main() -> int:
    out = ROOT / "outputs" / "mlops"
    out.mkdir(parents=True, exist_ok=True)
    raw = _generate_dataset()
    dq = validate_quality(raw, DataQualityConfig())
    (out / "data_quality_report.json").write_text(json.dumps(dq, ensure_ascii=True, indent=2), encoding="utf-8")
    if not dq.get("ok", False):
        print(json.dumps(dq, ensure_ascii=True, indent=2))
        return 1
    feats = build_features(raw)
    meta = register_snapshot(feats, out / "feature_registry", "market_features")
    result = {"ok": True, "data_quality": dq, "registry": meta}
    (out / "pipeline_result.json").write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
    append_experiment("mlops_data_pipeline", {"result": result}, run_id="", out_dir=out)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
