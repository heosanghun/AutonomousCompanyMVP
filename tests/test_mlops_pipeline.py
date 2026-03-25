import unittest

import numpy as np

from src.mlops.data_pipeline import DataQualityConfig, build_features, validate_quality


class TestMLOpsPipeline(unittest.TestCase):
    def test_quality_and_features(self) -> None:
        raw = np.array([[0.01], [0.02], [0.0], [-0.01], [0.03]], dtype=np.float32)
        q = validate_quality(raw, DataQualityConfig())
        self.assertTrue(q["ok"])
        feats = build_features(raw)
        self.assertEqual(feats.shape[1], 3)


if __name__ == "__main__":
    unittest.main()
