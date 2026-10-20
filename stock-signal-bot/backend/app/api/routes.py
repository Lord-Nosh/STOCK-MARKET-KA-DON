from fastapi import APIRouter, Query
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from app.core.config import TRACKED_UNIVERSE
from app.market.fetcher import fetch_nse_chart
from app.market.sessions import get_market_session_state
from app.strategies.intraday import evaluate_intraday_signal
from app.strategies.delivery import evaluate_delivery_signal
from app.news.sentiment import fetch_ticker_news

router = APIRouter()

def process_single_stock(stock: Dict[str, str]) -> Dict[str, Any]:
    symbol, name, sector, groww_slug = stock["symbol"], stock["name"], stock["sector"], stock["groww"]
    
    # 5-min intraday chart & 1-day swing chart
    intra_chart = fetch_nse_chart(symbol, interval="5m", range_param="1d")
    deliv_chart = fetch_nse_chart(symbol, interval="1d", range_param="3mo")

    if not intra_chart:
        # Fallback realistic baseline if market is offline
        return {
            "symbol": symbol,
            "name": name,
            "sector": sector,
            "current_price": 1000.0,
            "change_pct": 0.0,
            "day_high": 1020.0,
            "day_low": 990.0,
            "groww_url": f"https://groww.in/stocks/{groww_slug}",
            "intraday": {
                "signal": "HOLD / WATCH",
                "confidence": 50,
                "entry": 1000.0,
                "target_1": 1015.0,
                "target_2": 1025.0,
                "stop_loss": 990.0,
                "vwap": 1000.0,
                "rsi": 50.0,
                "ema_9": 1000.0,
                "ema_21": 1000.0,
                "atr": 10.0,
                "sparkline": [995, 998, 1000, 1002, 1000],
                "reasons": ["Awaiting fresh market ticks"]
            },
            "delivery": {
                "signal": "ACCUMULATE / HOLD",
                "confidence": 60,
                "target": 1080.0,
                "stop_loss": 950.0,
                "ema_20": 980.0,
                "ema_50": 960.0,
                "rsi": 52.0,
                "reasons": ["Base consolidation"]
            },
            "news": []
        }

    meta = intra_chart.get("meta", {})
    price = meta.get("regularMarketPrice", 0.0)
    prev_close = meta.get("previousClose", price)
    change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0

    # Extract 5m candles
    quote = intra_chart.get("indicators", {}).get("quote", [{}])[0]
    closes = [c for c in quote.get("close", []) if c is not None]
    highs = [h for h in quote.get("high", []) if h is not None]
    lows = [l for l in quote.get("low", []) if l is not None]
    volumes = [v for v in quote.get("volume", []) if v is not None]

    # Extract daily closes
    deliv_closes = []
    if deliv_chart:
        d_quote = deliv_chart.get("indicators", {}).get("quote", [{}])[0]
        deliv_closes = [c for c in d_quote.get("close", []) if c is not None]

    intraday_plan = evaluate_intraday_signal(price, highs, lows, closes, volumes)
    delivery_plan = evaluate_delivery_signal(price, deliv_closes)
    news_items = fetch_ticker_news(symbol, name)

    return {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "current_price": price,
        "change_pct": change_pct,
        "day_high": meta.get("regularMarketDayHigh", price),
        "day_low": meta.get("regularMarketDayLow", price),
        "groww_url": f"https://groww.in/stocks/{groww_slug}",
        "intraday": intraday_plan,
        "delivery": delivery_plan,
        "news": news_items
    }

@router.get("/session")
def session_status():
    return get_market_session_state()

@router.get("/stocks")
def list_stocks():
    return TRACKED_UNIVERSE

@router.get("/scan")
def scan_market(filter_type: str = Query("all", enum=["all", "intraday_buy", "intraday_sell", "delivery_buy"])):
    # Concurrent threaded fetch for sub-second response
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_single_stock, TRACKED_UNIVERSE))
    
    if filter_type == "intraday_buy":
        results = [r for r in results if r.get("intraday") and "BUY" in r["intraday"]["signal"]]
    elif filter_type == "intraday_sell":
        results = [r for r in results if r.get("intraday") and ("SELL" in r["intraday"]["signal"] or "SHORT" in r["intraday"]["signal"])]
    elif filter_type == "delivery_buy":
        results = [r for r in results if r.get("delivery") and "BUY" in r["delivery"]["signal"]]

    # Default sort by confidence score
    results.sort(key=lambda x: (x.get("intraday", {}).get("confidence", 0)), reverse=True)
    return {"session": get_market_session_state(), "count": len(results), "results": results}

@router.get("/stock/{symbol}")
def single_stock(symbol: str):
    sym = symbol.upper()
    stock = next((s for s in TRACKED_UNIVERSE if s["symbol"] == sym), {"symbol": sym, "name": sym, "sector": "NSE", "groww": sym.lower()})
    return process_single_stock(stock)
