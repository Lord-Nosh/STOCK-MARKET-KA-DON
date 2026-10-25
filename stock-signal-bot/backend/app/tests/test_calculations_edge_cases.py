import sys
import os
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.indicators.calculations import compute_intraday_levels, calculate_trade_risk_and_sizing
from app.core.config import ACCOUNT_CAPITAL, MIN_RISK_REWARD_RATIO


class TestCalculationsEdgeCases(unittest.TestCase):
    def test_compute_intraday_levels_unknown_signal_defaults_to_research_buy_levels(self):
        entry, t1, t2, sl = compute_intraday_levels(price=100.0, atr=2.0, signal_type="UNKNOWN")
        self.assertEqual(entry, 100.0)
        self.assertLess(sl, entry)
        self.assertGreater(t1, entry)
        self.assertGreater(t2, t1)

    def test_compute_intraday_levels_rejects_zero_price(self):
        with self.assertRaises(ValueError):
            compute_intraday_levels(price=0.0, atr=1.0, signal_type="BUY")

    def test_compute_intraday_levels_rejects_negative_atr(self):
        with self.assertRaises(ValueError):
            compute_intraday_levels(price=100.0, atr=-5.0, signal_type="SELL")

    def test_zero_risk_distance_is_rejected_for_sizing(self):
        sizing = calculate_trade_risk_and_sizing(
            entry_price=100.0, stop_loss=100.0, target_1=102.0, target_2=104.0,
            capital=ACCOUNT_CAPITAL,
        )
        self.assertEqual(sizing["shares_qty"], 0)
        self.assertFalse(sizing["trade_allowed"])
        self.assertFalse(sizing["passes_rr_filter"])
        self.assertEqual(sizing["rejection_reason"], "INVALID_STOP_DISTANCE")

    def test_calculate_trade_risk_and_sizing_high_margin(self):
        low_capital = 1000.0
        sizing = calculate_trade_risk_and_sizing(
            entry_price=200.0, stop_loss=195.0, target_1=210.0, target_2=220.0,
            capital=low_capital,
        )
        self.assertLessEqual(sizing["margin_required"], low_capital)
        self.assertGreaterEqual(sizing["shares_qty"], 1)

    def test_calculate_trade_risk_and_sizing_rr_filter(self):
        sizing = calculate_trade_risk_and_sizing(
            entry_price=100.0, stop_loss=99.0, target_1=100.5, target_2=101.0,
            capital=ACCOUNT_CAPITAL,
        )
        self.assertFalse(sizing["passes_rr_filter"])
        self.assertFalse(sizing["trade_allowed"])
        rr = float(sizing["risk_reward_ratio"].split(":")[1])
        self.assertLess(rr, MIN_RISK_REWARD_RATIO)

    def test_no_forced_one_share_when_risk_budget_is_too_small(self):
        sizing = calculate_trade_risk_and_sizing(
            entry_price=10000.0, stop_loss=9900.0, target_1=10200.0, target_2=10300.0,
            capital=1000.0,
        )
        self.assertEqual(sizing["shares_qty"], 0)
        self.assertLessEqual(sizing["actual_risk_inr"], sizing["allowable_risk_inr"])
        self.assertFalse(sizing["trade_allowed"])


if __name__ == "__main__":
    unittest.main()
