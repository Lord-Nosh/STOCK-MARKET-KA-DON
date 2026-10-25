# Tests for market data integrity handling in API routes
import unittest
import sys, os
# Ensure the backend app package is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from fastapi.testclient import TestClient
from app.api.routes import router
from app.core.config import TRACKED_UNIVERSE

class TestMarketDataIntegrity(unittest.TestCase):
    def setUp(self):
        # FastAPI app with only the router under test
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_single_stock_fails_when_market_data_unavailable(self):
        """Individual stock endpoint must return HTTP 503 when its market data is unavailable"""
        from app.departments.market_data.service import market_data_dep
        original_get = market_data_dep.get_stock_data
        market_data_dep.get_stock_data = lambda s, t: None
        try:
            response = self.client.get("/stock/RELIANCE")
            self.assertEqual(response.status_code, 503)
            self.assertIn("Market data unavailable for symbol RELIANCE", response.text)
        finally:
            market_data_dep.get_stock_data = original_get

    def test_scan_partial_resilience_when_one_stock_fails(self):
        """Batch scan must succeed with partial results if one stock fails"""
        from app.departments.market_data.service import market_data_dep
        original_get = market_data_dep.get_stock_data
        fail_sym = TRACKED_UNIVERSE[0]["symbol"]
        def mock_get(symbol: str, ticker: str):
            if symbol == fail_sym:
                return None
            return original_get(symbol, ticker)
        market_data_dep.get_stock_data = mock_get
        try:
            response = self.client.get("/scan")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data.get("is_partial"))
            self.assertIn(fail_sym, data.get("failed_symbols", []))
            self.assertEqual(data.get("count"), len(TRACKED_UNIVERSE) - 1)
            # Ensure failed stock is NOT in successful results
            result_syms = [r["symbol"] for r in data["results"]]
            self.assertNotIn(fail_sym, result_syms)
        finally:
            market_data_dep.get_stock_data = original_get

    def test_scan_fails_503_when_all_stocks_fail(self):
        """Batch scan must return HTTP 503 if every single stock fails to provide data"""
        from app.departments.market_data.service import market_data_dep
        original_get = market_data_dep.get_stock_data
        market_data_dep.get_stock_data = lambda s, t: None
        try:
            response = self.client.get("/scan")
            self.assertEqual(response.status_code, 503)
            self.assertIn("Market data unavailable for all", response.text)
        finally:
            market_data_dep.get_stock_data = original_get

if __name__ == "__main__":
    unittest.main()
