import sys, os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.indicators.calculations import compute_intraday_levels, calculate_trade_risk_and_sizing
from app.core.config import ACCOUNT_CAPITAL, RISK_PER_TRADE_PCT, MIN_RISK_REWARD_RATIO

import unittest

class TestCalculationsEdgeCases(unittest.TestCase):

    def test_compute_intraday_levels_invalid_signal(self):
        # Signal type not containing BUY or SELL should default to BUY logic
        entry, t1, t2, sl = compute_intraday_levels(price=100.0, atr=2.0, signal_type="UNKNOWN")
        self.assertEqual(entry, 100.0)
        self.assertLess(sl, entry)  # default is BUY (sl below entry)
        self.assertGreater(t1, entry)
        self.assertGreater(t2, t1)

    def test_compute_intraday_levels_zero_price(self):
        # Zero price should not cause division errors; risk computed from ATR
        entry, t1, t2, sl = compute_intraday_levels(price=0.0, atr=1.0, signal_type="BUY")
        self.assertEqual(entry, 0.0)
        self.assertLess(sl, entry)
        self.assertGreater(t1, entry)
        self.assertGreater(t2, t1)

    def test_compute_intraday_levels_negative_atr(self):
        # Negative ATR treated as absolute value in risk calculation (risk = max(atr*1.5, ...))
        entry, t1, t2, sl = compute_intraday_levels(price=100.0, atr=-5.0, signal_type="SELL")
        # Risk uses atr*1.5 = -7.5, but max with price*0.005 (=0.5) => risk = 0.5
        self.assertEqual(sl, round(100.0 + 0.5, 2))
        self.assertLess(t1, entry)
        self.assertLess(t2, t1)

    def test_calculate_trade_risk_and_sizing_invalid_risk(self):
        # Zero risk distance should fallback to minimum risk
        sizing = calculate_trade_risk_and_sizing(entry_price=100.0, stop_loss=100.0, target_1=102.0, target_2=104.0, capital=ACCOUNT_CAPITAL)
        # shares should be based on minimum risk distance 0.5% of entry (0.5) -> allowable risk ~ 90 => 180 shares approx
        self.assertGreaterEqual(sizing["shares_qty"], 1)
        self.assertLessEqual(sizing["actual_risk_inr"], sizing["allowable_risk_inr"])
        self.assertTrue(sizing["passes_rr_filter"])

    def test_calculate_trade_risk_and_sizing_high_margin(self):
        # Capital too low for required margin; expect shares reduced
        low_capital = 1000.0
        sizing = calculate_trade_risk_and_sizing(entry_price=200.0, stop_loss=195.0, target_1=210.0, target_2=220.0, capital=low_capital)
        self.assertLessEqual(sizing["margin_required"], low_capital)
        self.assertGreaterEqual(sizing["shares_qty"], 1)

    def test_calculate_trade_risk_and_sizing_rr_filter(self):
        # Provide a trade with poor R:R; should fail filter
        sizing = calculate_trade_risk_and_sizing(entry_price=100.0, stop_loss=99.0, target_1=100.5, target_2=101.0, capital=ACCOUNT_CAPITAL)
        self.assertFalse(sizing["passes_rr_filter"])
        # Ensure risk-reward ratio reflects poor value (< MIN_RISK_REWARD_RATIO)
        rr = float(sizing["risk_reward_ratio"].split(":")[1])
        self.assertLess(rr, MIN_RISK_REWARD_RATIO)

if __name__ == "__main__":
    unittest.main()
