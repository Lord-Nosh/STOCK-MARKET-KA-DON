import math
import os
import time
import json
import urllib.request
from typing import Dict, Any, Optional

from app.departments.market_data.replay_harness import ReplayMarketDataProvider


class MarketDataDepartment:
    """
    Single shared market-data source for downstream analysis.

    Current online provider remains the public Yahoo Finance chart endpoint;
    it is deliberately marked UNVERIFIED_PUBLIC_PROVIDER and is not authorized
    to produce execution-eligible signals. Plug in a licensed broker/exchange
    adapter before enabling actionable signals.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry: Dict[str, float] = {}

    def get_stock_data(self, symbol: str, ticker: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        cache_key = f"{os.getenv('SMKD_DATA_MODE', 'live').lower()}:{ticker}"
        if cache_key in self._cache and (now - self._cache_expiry.get(cache_key, 0)) < 10:
            return self._cache[cache_key]

        chart_5m = self._fetch_chart(ticker, interval="5m", range_param="1d")
        chart_daily = self._fetch_chart(ticker, interval="1d", range_param="3mo")
        if not chart_5m:
            return None

        meta = chart_5m.get("meta") or {}
        try:
            price = float(meta.get("regularMarketPrice"))
        except (TypeError, ValueError):
            return None
        if not math.isfinite(price) or price <= 0:
            return None

        prev_close_raw = meta.get("previousClose", price)
        try:
            prev_close = float(prev_close_raw) if prev_close_raw is not None else price
        except (TypeError, ValueError):
            prev_close = price
        change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close > 0 else 0.0

        quote_5m = ((chart_5m.get("indicators") or {}).get("quote") or [{}])[0] or {}
        timestamps_5m = chart_5m.get("timestamp") or []
        candles = self._validated_candles(quote_5m, timestamps_5m)
        daily_closes = self._validated_daily_closes(chart_daily)
        if not candles["closes"]:
            # Don't create technical indicators from empty or row-misaligned OHLCV.
            return None

        mode = os.getenv("SMKD_DATA_MODE", "live").lower()
        is_replay = mode == "replay"
        provider_timestamp = meta.get("regularMarketTime") or candles["timestamps"][-1]
        payload = {
            "symbol": symbol,
            "ticker": ticker,
            "current_price": price,
            "change_pct": change_pct,
            "day_high": self._finite_positive(meta.get("regularMarketDayHigh"), price),
            "day_low": self._finite_positive(meta.get("regularMarketDayLow"), price),
            "volume_today": self._finite_nonnegative(meta.get("regularMarketVolume"), sum(candles["volumes"])),
            # timestamp is retained as processing/receipt time for old clients.
            "timestamp": now,
            "received_at": now,
            "provider_timestamp": provider_timestamp,
            "data_source": "FIXTURE_REPLAY" if is_replay else "YAHOO_FINANCE_UNOFFICIAL",
            "data_mode": "SIMULATED" if is_replay else "UNVERIFIED_PUBLIC_PROVIDER",
            "signal_eligible": False,
            "data_quality": {
                "complete_candle_count": len(candles["closes"]),
                "latest_candle_timestamp": candles["timestamps"][-1],
                "incomplete_candles_dropped": candles["dropped"],
                "ohlcv_arrays_aligned": True,
            },
            "candles_5m": {key: value for key, value in candles.items() if key != "dropped"},
            "candles_daily": {"closes": daily_closes},
        }

        self._cache[cache_key] = payload
        self._cache_expiry[cache_key] = now
        return payload

    @staticmethod
    def _finite_positive(value: Any, fallback: float) -> float:
        try:
            converted = float(value)
        except (TypeError, ValueError):
            return fallback
        return converted if math.isfinite(converted) and converted > 0 else fallback

    @staticmethod
    def _finite_nonnegative(value: Any, fallback: float) -> float:
        try:
            converted = float(value)
        except (TypeError, ValueError):
            return fallback
        return converted if math.isfinite(converted) and converted >= 0 else fallback

    @staticmethod
    def _validated_candles(quote: Dict[str, Any], timestamps: list) -> Dict[str, Any]:
        fields = ("open", "high", "low", "close", "volume")
        arrays = {name: quote.get(name) or [] for name in fields}
        row_count = min([len(timestamps)] + [len(arrays[name]) for name in fields]) if timestamps else 0
        accepted = {name: [] for name in fields}
        accepted_timestamps = []
        dropped = 0

        for index in range(row_count):
            try:
                values = {name: float(arrays[name][index]) for name in fields}
                timestamp = int(timestamps[index])
            except (TypeError, ValueError, OverflowError):
                dropped += 1
                continue

            o, h, low, close, volume = (
                values["open"], values["high"], values["low"], values["close"], values["volume"]
            )
            if (
                not all(math.isfinite(value) for value in values.values())
                or timestamp <= 0
                or min(o, h, low, close) <= 0
                or volume < 0
                or not (low <= o <= h and low <= close <= h)
            ):
                dropped += 1
                continue

            for name in fields:
                accepted[name].append(int(volume) if name == "volume" else values[name])
            accepted_timestamps.append(timestamp)

        # Differently sized provider arrays represent incomplete bars. Do not zip
        # longer timestamps against shorter OHLCV arrays and mislabel the candles.
        if any(len(arrays[name]) != len(timestamps) for name in fields):
            dropped += max([len(timestamps)] + [len(arrays[name]) for name in fields]) - row_count

        return {
            "opens": accepted["open"],
            "highs": accepted["high"],
            "lows": accepted["low"],
            "closes": accepted["close"],
            "volumes": accepted["volume"],
            "timestamps": accepted_timestamps,
            "dropped": dropped,
        }

    @staticmethod
    def _validated_daily_closes(chart_daily: Optional[Dict[str, Any]]) -> list:
        if not chart_daily:
            return []
        quote_items = ((chart_daily.get("indicators") or {}).get("quote") or [{}])
        if not quote_items:
            return []
        closes = quote_items[0].get("close") or []
        return [
            float(value)
            for value in closes
            if value is not None and isinstance(value, (int, float)) and math.isfinite(value) and value > 0
        ]

    def _fetch_chart(self, ticker: str, interval: str, range_param: str) -> Optional[Dict[str, Any]]:
        if os.getenv("SMKD_DATA_MODE", "live").lower() == "replay":
            replay_provider = ReplayMarketDataProvider(mode="replay")
            return replay_provider.fetch_replay_chart(ticker)

        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{ticker}?interval={interval}&range={range_param}"
        )
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "SMKD-research-client/2.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            result = (data.get("chart") or {}).get("result") or []
            return result[0] if result else None
        except (OSError, ValueError, json.JSONDecodeError):
            return None


market_data_dep = MarketDataDepartment()
