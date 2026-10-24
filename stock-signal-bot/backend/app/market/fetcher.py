import json
import urllib.request
from typing import Optional, Dict, Any

def fetch_nse_chart(ticker_or_symbol: str, interval: str, range_param: str) -> Optional[Dict[str, Any]]:
    """Fetches clean OHLCV candle payloads for Indian NSE equities (.NS)"""
    if ticker_or_symbol.startswith("^"):
        ticker = ticker_or_symbol
    else:
        ticker = ticker_or_symbol if ticker_or_symbol.endswith(".NS") else f"{ticker_or_symbol}.NS"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={range_param}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            results = data.get("chart", {}).get("result")
            if results and len(results) > 0:
                return results[0]
    except Exception as e:
        print(f"[MarketFetcher] Error for {ticker}: {e}")
    return None
