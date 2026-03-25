import unittest

from src.risk.guard import RiskConfig, RiskGuard


class TestRiskGuard(unittest.TestCase):
    def test_daily_loss_triggers_kill_switch(self) -> None:
        rg = RiskGuard(RiskConfig(max_daily_loss=0.01))
        out = rg.evaluate(action=2, realized_pnl=0.0, day_pnl=-0.02, volatility=0.01)
        self.assertEqual(out, 1)
        self.assertTrue(rg.kill_switch)
        self.assertEqual(rg.last_reason, "max_daily_loss")

    def test_volatility_blocks_action(self) -> None:
        rg = RiskGuard(RiskConfig(hard_volatility_breaker=0.05))
        out = rg.evaluate(action=2, realized_pnl=0.0, day_pnl=0.0, volatility=0.1)
        self.assertEqual(out, 1)
        self.assertEqual(rg.last_reason, "hard_volatility_breaker")

    def test_weekly_loss_triggers_kill_switch(self) -> None:
        rg = RiskGuard(RiskConfig(max_weekly_loss=0.01))
        out = rg.evaluate(action=2, realized_pnl=0.0, day_pnl=0.0, volatility=0.01, week_pnl=-0.02)
        self.assertEqual(out, 1)
        self.assertTrue(rg.kill_switch)
        self.assertEqual(rg.last_reason, "max_weekly_loss")


if __name__ == "__main__":
    unittest.main()
