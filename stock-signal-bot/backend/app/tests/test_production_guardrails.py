import os
import time
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router
from app.departments.market_data.feed_integrity import FeedMode, enrich_with_provenance
from app.departments.market_data.service import MarketDataDepartment


class TestProductionGuardrails(unittest.TestCase):
    def test_incomplete_ohlcv_rows_are_filtered_together(self):
        chart = {
            "timestamp": [100, 200, 300],
            "open": [10.0, None, 12.0],
            "high": [11.0, 13.0, None],
            "low": [9.0, 8.0, 11.0],
            "close": [10.5, None, 12.5],
            "volume": [100, 200, 300],
        }
        result = MarketDataDepartment._validated_candles(chart, chart["timestamp"])
        self.assertEqual(result["closes"], [10.5])
        self.assertEqual(result["timestamps"], [100])
        self.assertEqual(len(result["opens"]), len(result["highs"]))
        self.assertEqual(len(result["highs"]), len(result["lows"]))
        self.assertEqual(len(result["lows"]), len(result["closes"]))
        self.assertEqual(len(result["closes"]), len(result["volumes"]))
        self.assertEqual(result["dropped"], 2)

    def test_stale_feed_provenance_matches_stale_flag(self):
        now = time.time()
        payload = enrich_with_provenance(
            symbol="TEST",
            raw={"exchange_timestamp": now - 120, "sequence_id": 4},
            source="TEST_FEED",
            mode=FeedMode.LIVE,
            connection_ok=True,
            last_msg_ts=now - 120,
        )
        provenance = payload["feed_provenance"]
        self.assertTrue(provenance["is_stale"])
        self.assertIsNotNone(provenance["stale_reason"])
        self.assertEqual(provenance["mode"], "DELAYED")

    def test_admin_endpoints_fail_closed_without_configured_key(self):
        previous = os.environ.pop("SMKD_ADMIN_API_KEY", None)
        try:
            app = FastAPI()
            app.include_router(router)
            response = TestClient(app).get("/system/backups")
            self.assertEqual(response.status_code, 503)
        finally:
            if previous is not None:
                os.environ["SMKD_ADMIN_API_KEY"] = previous

    def test_invalid_capital_is_rejected_by_sizing(self):
        from app.indicators.calculations import calculate_trade_risk_and_sizing
        with self.assertRaises(ValueError):
            calculate_trade_risk_and_sizing(
                entry_price=100.0,
                stop_loss=99.0,
                target_1=102.0,
                target_2=103.0,
                capital=0.0,
            )


if __name__ == "__main__":
    unittest.main()
