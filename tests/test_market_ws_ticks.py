import unittest

from src.data.market_data import ws_prices_to_ticks_returns


class TestWsPricesToTicks(unittest.TestCase):
    def test_shapes(self) -> None:
        prices = [100.0, 101.0, 100.5, 102.0]
        ticks, ret = ws_prices_to_ticks_returns(prices)
        self.assertEqual(len(ticks), len(ret))
        self.assertEqual(ticks.shape[1], 3)
        self.assertEqual(float(ret[0]), 0.0)


if __name__ == "__main__":
    unittest.main()
