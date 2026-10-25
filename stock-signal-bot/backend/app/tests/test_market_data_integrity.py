import os
import sys
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import routes as routes_module
from app.api.routes import router
from app.core.config import TRACKED_UNIVERSE


class TestMarketDataIntegrity(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self.original_intelligence = routes_module.market_intelligence_dep.get_intelligence
        routes_module.market_intelligence_dep.get_intelligence = lambda: {
            "session": {"phase": "TEST", "ist_time": "10:00:00 IST"},
            "nifty_50": {"trend": "SIDEWAYS"},
        }

    def tearDown(self):
        routes_module.market_intelligence_dep.get_intelligence = self.original_intelligence

    def test_single_stock_fails_when_market_data_unavailable(self):
        from app.departments.market_data.service import market_data_dep
        original_get = market_data_dep.get_stock_data
        market_data_dep.get_stock_data = lambda symbol, ticker: None
        try:
            response = self.client.get("/stock/RELIANCE")
            self.assertEqual(response.status_code, 503)
            self.assertIn("Market data unavailable for symbol RELIANCE", response.text)
        finally:
            market_data_dep.get_stock_data = original_get

    def test_scan_partial_resilience_when_one_stock_fails(self):
        original_process = routes_module.process_unified_stock
        fail_symbol = TRACKED_UNIVERSE[0]["symbol"]

        def fake_process(stock, intelligence, capital):
            if stock["symbol"] == fail_symbol:
                return None
            return {
                "symbol": stock["symbol"],
                "name": stock["name"],
                "sector": stock["sector"],
                "current_price": 100.0,
                "change_pct": 0.0,
                "intraday": {"signal": "SCANNING", "confidence": 50},
                "signal_decision": {"confluence_score": 1},
                "news": [],
            }

        routes_module.process_unified_stock = fake_process
        try:
            response = self.client.get("/scan")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data.get("is_partial"))
            self.assertIn(fail_symbol, data.get("failed_symbols", []))
            self.assertEqual(data.get("count"), len(TRACKED_UNIVERSE) - 1)
            result_symbols = [result["symbol"] for result in data["results"]]
            self.assertNotIn(fail_symbol, result_symbols)
        finally:
            routes_module.process_unified_stock = original_process

    def test_scan_fails_503_when_all_stocks_fail(self):
        original_process = routes_module.process_unified_stock
        routes_module.process_unified_stock = lambda stock, intelligence, capital: None
        try:
            response = self.client.get("/scan")
            self.assertEqual(response.status_code, 503)
            self.assertIn("Market data unavailable for all", response.text)
        finally:
            routes_module.process_unified_stock = original_process

    def test_non_positive_capital_is_rejected(self):
        response = self.client.get("/scan?capital=0")
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
