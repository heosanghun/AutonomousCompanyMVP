import unittest

from src.execution.broker import PaperBroker
from src.execution.order_router import OrderRouter, RouterConfig


class TestOrderRouterNotional(unittest.TestCase):
    def test_per_order_notional_blocks_submit(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            b = PaperBroker(f"{td}/fills.jsonl")
            r = OrderRouter(
                b,
                RouterConfig(
                    mode="paper",
                    symbol="BTCUSDT",
                    default_qty=1.0,
                    max_notional_usd_per_order=10.0,
                ),
            )
            fill = r.submit_action(
                action=2,
                price_hint=100.0,
                decision_id="d1",
                reason_code="t",
                risk_approved=True,
                feature_row=[0.0, 0.0, 0.0],
            )
            self.assertIsNone(fill)
            self.assertEqual(r.last_reject_reason, "max_notional_usd_per_order")


if __name__ == "__main__":
    unittest.main()
