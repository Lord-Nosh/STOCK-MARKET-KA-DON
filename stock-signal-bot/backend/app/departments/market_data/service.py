import time
import json
import os
import urllib.request
from typing import Dict, Any, List, Optional
from app.core.config import TRACKED_UNIVERSE
from app.departments.market_data.replay_harness import ReplayMarketDataProvider

class MarketDataDepartment:
    """
    DEPARTMENT 1: MARKET DATA
    Responsibility: Live prices, 5-minute candles, daily candles, volume, and tick history.
    Single shared source of truth for all downstream analysis departments.
    """
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry: Dict[str, float] = {}

    def get_stock_data(self, symbol: str, ticker: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        # 10 second memory caching for live candles
        if ticker in self._cache and (now - self._cache_expiry.get(ticker, 0)) < 10:
            return self._cache[ticker]

        chart_5m = self._fetch_chart(ticker, interval="5m", range_param="1d")
        chart_daily = self._fetch_chart(ticker, interval="1d", range_param="3mo")

        if not chart_5m:
            return None

        meta = chart_5m.get("meta", {})
        price = meta.get("regularMarketPrice", 0.0)
        prev_close = meta.get("previousClose", price)
        change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0

        quote_5m = chart_5m.get("indicators", {}).get("quote", [{}])[0]
        timestamps_5m = chart_5m.get("timestamp", [])

        opens_5m = [o for o in quote_5m.get("open", []) if o is not None]
        highs_5m = [h for h in quote_5m.get("high", []) if h is not None]
        lows_5m = [l for l in quote_5m.get("low", []) if l is not None]
        closes_5m = [c for c in quote_5m.get("close", []) if c is not None]
        volumes_5m = [v for v in quote_5m.get("volume", []) if v is not None]

        # Extract daily candles
        daily_closes = []
        if chart_daily:
            d_quote = chart_daily.get("indicators", {}).get("quote", [{}])[0]
            daily_closes = [c for c in d_quote.get("close", []) if c is not None]

        payload = {
            "symbol": symbol,
            "ticker": ticker,
            "current_price": price,
            "change_pct": change_pct,
            "day_high": meta.get("regularMarketDayHigh", price),
            "day_low": meta.get("regularMarketDayLow", price),
            "volume_today": meta.get("regularMarketVolume", sum(volumes_5m) if volumes_5m else 0),
            "timestamp": now,
            "candles_5m": {
                "opens": opens_5m,
                "highs": highs_5m,
                "lows": lows_5m,
                "closes": closes_5m,
                "volumes": volumes_5m,
                "timestamps": timestamps_5m[-len(closes_5m):] if timestamps_5m else []
            },
            "candles_daily": {
                "closes": daily_closes
            }
        }

        self._cache[ticker] = payload
        self._cache_expiry[ticker] = now
        return payload

    def _fetch_chart(self, ticker: str, interval: str, range_param: str) -> Optional[Dict[str, Any]]:
        if os.getenv("SMKD_DATA_MODE") == "replay":
            replay_provider = ReplayMarketDataProvider(mode="replay")
            return replay_provider.fetch_replay_chart(ticker)

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={range_param}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                res = data.get("chart", {}).get("result")
                if res and len(res) > 0:
                    return res[0]
        except Exception:
            pass
        return None

market_data_dep = MarketDataDepartment()
