import json
import urllib.request
from typing import List, Dict, Any
from app.indicators.technicals import calculate_rsi, calculate_ema, calculate_vwap, calculate_atr
from app.indicators.calculations import compute_intraday_levels

def run_historical_backtest(symbol: str, days: int = 5) -> Dict[str, Any]:
    """
    Backtests the exact intraday strategy on historical 5-minute candles over the past N trading sessions.
    Simulates real execution: checks if Target 1, Target 2, or Stop Loss gets touched first on subsequent bars.
    """
    ticker = f"{symbol}.NS"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=5m&range={days}d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            res = data.get("chart", {}).get("result", [])[0]
    except Exception as e:
        return {"error": f"Failed to retrieve backtest series: {e}"}

    quote = res.get("indicators", {}).get("quote", [{}])[0]
    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    closes = quote.get("close", [])
    volumes = quote.get("volume", [])
    timestamps = res.get("timestamp", [])

    # Filter out empty bars
    valid_bars = []
    for i in range(len(closes)):
        if closes[i] is not None and highs[i] is not None and lows[i] is not None:
            valid_bars.append({
                "index": i,
                "open": opens[i],
                "high": highs[i],
                "low": lows[i],
                "close": closes[i],
                "volume": volumes[i] if i < len(volumes) and volumes[i] else 1000,
                "time": timestamps[i] if i < len(timestamps) else 0
            })

    if len(valid_bars) < 30:
        return {"error": "Insufficient historical candles for backtesting"}

    trades = []
    # Warmup period of 25 bars for indicators
    for i in range(25, len(valid_bars) - 10):
        window_highs = [b["high"] for b in valid_bars[:i+1]]
        window_lows = [b["low"] for b in valid_bars[:i+1]]
        window_closes = [b["close"] for b in valid_bars[:i+1]]
        window_vols = [b["volume"] for b in valid_bars[:i+1]]

        c_price = window_closes[-1]
        rsi = calculate_rsi(window_closes, 14)
        ema_9 = calculate_ema(window_closes, 9)
        ema_21 = calculate_ema(window_closes, 21)
        vwap = calculate_vwap(window_highs[-40:], window_lows[-40:], window_closes[-40:], window_vols[-40:])
        atr = calculate_atr(window_highs, window_lows, window_closes, 14)

        # Signal check
        is_buy = c_price > vwap and ema_9 > ema_21 and 52 <= rsi <= 70
        is_sell = c_price < vwap and ema_9 < ema_21 and 30 <= rsi <= 48

        if not is_buy and not is_sell:
            continue

        signal_type = "BUY" if is_buy else "SELL"
        entry, t1, t2, sl = compute_intraday_levels(c_price, atr, signal_type)

        # Forward simulate on subsequent candles (up to 15 bars / ~75 minutes)
        outcome = "TIME_EXPIRED"
        pnl_pct = 0.0
        exit_price = c_price
        bars_held = 0

        for fwd in range(1, 16):
            if i + fwd >= len(valid_bars):
                break
            f_bar = valid_bars[i + fwd]
            bars_held = fwd

            if signal_type == "BUY":
                # Check Stop Loss first (conservative)
                if f_bar["low"] <= sl:
                    outcome = "STOP_LOSS_HIT"
                    exit_price = sl
                    pnl_pct = round(((sl - entry) / entry) * 100, 2)
                    break
                elif f_bar["high"] >= t2:
                    outcome = "TARGET_2_HIT"
                    exit_price = t2
                    pnl_pct = round(((t2 - entry) / entry) * 100, 2)
                    break
                elif f_bar["high"] >= t1:
                    outcome = "TARGET_1_HIT"
                    exit_price = t1
                    pnl_pct = round(((t1 - entry) / entry) * 100, 2)
                    break
            else: # SELL
                if f_bar["high"] >= sl:
                    outcome = "STOP_LOSS_HIT"
                    exit_price = sl
                    pnl_pct = round(((entry - sl) / entry) * 100, 2)
                    break
                elif f_bar["low"] <= t2:
                    outcome = "TARGET_2_HIT"
                    exit_price = t2
                    pnl_pct = round(((entry - t2) / entry) * 100, 2)
                    break
                elif f_bar["low"] <= t1:
                    outcome = "TARGET_1_HIT"
                    exit_price = t1
                    pnl_pct = round(((entry - t1) / entry) * 100, 2)
                    break

        if outcome == "TIME_EXPIRED" and i + bars_held < len(valid_bars):
            exit_price = valid_bars[i + bars_held]["close"]
            pnl_pct = round(((exit_price - entry) / entry) * 100, 2) if signal_type == "BUY" else round(((entry - exit_price) / entry) * 100, 2)

        trades.append({
            "bar_index": i,
            "signal": signal_type,
            "entry": entry,
            "exit": exit_price,
            "target_1": t1,
            "stop_loss": sl,
            "outcome": outcome,
            "pnl_pct": pnl_pct,
            "bars_held": bars_held
        })

    # Summary Statistics
    total_trades = len(trades)
    if total_trades == 0:
        return {"symbol": symbol, "total_trades": 0, "message": "No clean breakouts during sample period"}

    wins = sum(1 for t in trades if t["outcome"] in ["TARGET_1_HIT", "TARGET_2_HIT"] or t["pnl_pct"] > 0)
    losses = sum(1 for t in trades if t["outcome"] == "STOP_LOSS_HIT" or t["pnl_pct"] < 0)
    win_rate = round((wins / total_trades) * 100, 1)
    avg_pnl = round(sum(t["pnl_pct"] for t in trades) / total_trades, 2)
    profit_factor = round((sum(t["pnl_pct"] for t in trades if t["pnl_pct"] > 0) / abs(sum(t["pnl_pct"] for t in trades if t["pnl_pct"] < 0) or 1)), 2)

    return {
        "symbol": symbol,
        "sample_period_days": days,
        "total_signals": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": win_rate,
        "avg_trade_pnl_pct": avg_pnl,
        "profit_factor": profit_factor,
        "recent_trades_sample": trades[-8:]  # Last 8 simulated trades
    }
