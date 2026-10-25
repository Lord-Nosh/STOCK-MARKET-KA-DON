import os
import unittest
from app.departments.market_data.service import MarketDataDepartment
from app.indicators.technicals import calculate_rsi


class TestMarketDataReplay(unittest.TestCase):
    def setUp(self):
        self.original_mode = os.environ.get("SMKD_DATA_MODE")
        os.environ["SMKD_DATA_MODE"] = "replay"
        self.service = MarketDataDepartment()

    def tearDown(self):
        if self.original_mode is not None:
            os.environ["SMKD_DATA_MODE"] = self.original_mode
        else:
            os.environ.pop("SMKD_DATA_MODE", None)

    def test_replay_valid_5m_fixture(self):
        """Valid fixture candles remain aligned and usable for research."""
        data = self.service.get_stock_data("RELIANCE", "RELIANCE.NS")
        self.assertIsNotNone(data)
        self.assertEqual(data["symbol"], "RELIANCE")
        self.assertEqual(data["current_price"], 2985.50)
        candles = data["candles_5m"]
        self.assertEqual(len(candles["closes"]), 15)
        self.assertEqual(len(candles["timestamps"]), 15)
        self.assertEqual(len(candles["opens"]), len(candles["highs"]))
        self.assertEqual(len(candles["highs"]), len(candles["lows"]))
        self.assertEqual(len(candles["lows"]), len(candles["closes"]))
        self.assertEqual(len(candles["closes"]), len(candles["volumes"]))
        self.assertFalse(data["signal_eligible"])
        self.assertEqual(data["data_mode"], "SIMULATED")

        rsi = calculate_rsi(candles["closes"])
        self.assertIsNotNone(rsi)
        self.assertGreater(rsi, 0.0)
        self.assertLess(rsi, 100.0)

    def test_replay_empty_history_is_rejected(self):
        """An empty candle set must not be turned into a stock signal payload."""
        data = self.service.get_stock_data("INFY", "INFY.NS")
        self.assertIsNone(data)
        self.assertIsNone(calculate_rsi([]))

    def test_replay_malformed_candles_are_rejected_as_rows(self):
        """A candle is accepted/rejected as a full row; individual arrays never drift."""
        data = self.service.get_stock_data("TCS", "TCS.NS")
        self.assertIsNone(data)  # Each row has at least one missing OHLCV field.


if __name__ == "__main__":
    unittest.main()
