import os
import json
from typing import Dict, Any, Optional

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "fixtures", "market_data")

class ReplayMarketDataProvider:
    """
    Deterministic Market Data Replay Provider for offline testing.
    Swaps out live HTTP network requests with verified provider fixture snapshots.
    """
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or os.getenv("SMKD_DATA_MODE", "live").lower()
        self._fixtures: Dict[str, Dict[str, Any]] = {}
        self._load_fixtures()

    def _load_fixtures(self):
        if not os.path.exists(FIXTURES_DIR):
            return
        for fname in os.listdir(FIXTURES_DIR):
            if fname.endswith(".json"):
                fpath = os.path.join(FIXTURES_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        key = data.get("ticker", data.get("symbol", fname.replace(".json", "")))
                        self._fixtures[key] = data
                        self._fixtures[fname.replace(".json", "")] = data
                except Exception:
                    pass

    @property
    def is_replay_mode(self) -> bool:
        return self.mode == "replay"

    def fetch_replay_chart(self, ticker: str, fixture_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if fixture_name and fixture_name in self._fixtures:
            return self._fixtures[fixture_name]
        return self._fixtures.get(ticker)
