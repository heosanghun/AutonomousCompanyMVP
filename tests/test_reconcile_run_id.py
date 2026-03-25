import json
import tempfile
import unittest
from pathlib import Path

from src.ops.reconcile import reconcile_counts


class TestReconcileRunId(unittest.TestCase):
    def test_filters_by_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            rid = "run-abc-123"
            fills = out / "fills.jsonl"
            fills.write_text(
                json.dumps({"run_id": "old", "x": 1}) + "\n"
                + json.dumps({"run_id": rid, "status": "filled"}) + "\n"
                + json.dumps({"run_id": rid, "status": "filled"}) + "\n",
                encoding="utf-8",
            )
            (out / "summary.json").write_text(
                json.dumps({"n_fills": 2, "run_id": rid}, ensure_ascii=True),
                encoding="utf-8",
            )
            r = reconcile_counts(out)
            self.assertTrue(r["ok"])
            self.assertEqual(r["observed_n_fills"], 2)
            self.assertEqual(r["expected_n_fills"], 2)


if __name__ == "__main__":
    unittest.main()
