import os
import unittest
from app.departments.market_data.service import MarketDataDepartment
from app.indicators.technicals import calculate_rsi, calculate_ema

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
        """Verifies deterministic parsing and calculations using offline replay fixture"""
        data = self.service.get_stock_data("RELIANCE", "RELIANCE.NS")
        self.assertIsNotNone(data)
        self.assertEqual(data["symbol"], "RELIANCE")
        self.assertEqual(data["current_price"], 2985.50)
        self.assertEqual(len(data["candles_5m"]["closes"]), 15)

        # Technical indicators calculate deterministically
        rsi = calculate_rsi(data["candles_5m"]["closes"])
        self.assertIsNotNone(rsi)
        self.assertGreater(rsi, 0.0)
        self.assertLess(rsi, 100.0)

    def test_replay_empty_history_fixture(self):
        """Verifies graceful handling of empty candles fixture"""
        data = self.service.get_stock_data("INFY", "INFY.NS")
        self.assertIsNotNone(data)
        self.assertEqual(len(data["candles_5m"]["closes"]), 0)

        # RSI returns None when insufficient candles
        rsi = calculate_rsi(data["candles_5m"]["closes"])
        self.assertIsNone(rsi)

    def test_replay_malformed_fixture_filters_nulls(self):
        """Verifies null values in OHLCV stream are stripped safely"""
        data = self.service.get_stock_data("TCS", "TCS.NS")
        self.assertIsNotNone(data)
        # 1 out of 3 closes was null in TCS fixture
        self.assertEqual(len(data["candles_5m"]["closes"]), 2)
        self.assertNotIn(None, data["candles_5m"]["closes"])

if __name__ == "__main__":
    unittest.main()
