from typing import List, Dict, Any
from app.indicators.technicals import calculate_rsi, calculate_ema, calculate_vwap, calculate_atr
from app.indicators.calculations import compute_intraday_levels

def evaluate_intraday_signal(
    current_price: float,
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float]
) -> Dict[str, Any]:
    """Generates 5-minute Intraday MIS signal with VWAP, EMA cross, ATR bounds and sparkline series"""
    rsi_14 = calculate_rsi(closes, 14) if len(closes) > 14 else 50.0
    ema_9 = calculate_ema(closes, 9)
    ema_21 = calculate_ema(closes, 21)
    vwap = calculate_vwap(highs, lows, closes, volumes) if closes else current_price
    atr = calculate_atr(highs, lows, closes, 14)

    reasons: List[str] = []
    signal_type = "HOLD / WATCH"
    confidence = 50

    # Bullish criteria
    if current_price > vwap and ema_9 > ema_21 and 52 <= rsi_14 <= 72:
        signal_type = "BUY (Intraday Momentum)"
        confidence = 82
        reasons.append(f"Price (₹{current_price}) holds strictly above VWAP (₹{vwap})")
        reasons.append(f"Bullish 9-EMA (₹{ema_9}) expansion above 21-EMA (₹{ema_21})")
        reasons.append(f"RSI ({rsi_14}) in confirmed momentum expansion range")
    # Bearish criteria
    elif current_price < vwap and ema_9 < ema_21 and 28 <= rsi_14 <= 48:
        signal_type = "SELL / SHORT (Intraday Breakdown)"
        confidence = 78
        reasons.append(f"Price (₹{current_price}) rejected below VWAP (₹{vwap})")
        reasons.append(f"Bearish 9-EMA slope under 21-EMA")
        reasons.append(f"RSI ({rsi_14}) showing seller dominance")
    elif rsi_14 > 75:
        signal_type = "OVERBOUGHT (Watch Reversal)"
        confidence = 65
        reasons.append(f"RSI ({rsi_14}) overbought; high risk of long trap near resistance")
    elif rsi_14 < 25:
        signal_type = "OVERSOLD (Watch Bounce)"
        confidence = 65
        reasons.append(f"RSI ({rsi_14}) oversold; mean reversion bounce probable near support")
    else:
        reasons.append(f"Rangebound consolidation around VWAP (₹{vwap})")

    entry, t1, t2, sl = compute_intraday_levels(current_price, atr, signal_type)

    # Clean last 20 normalized points for sparkline rendering
    sparkline = [round(c, 2) for c in closes[-20:]] if closes else [current_price] * 10

    return {
        "signal": signal_type,
        "confidence": confidence,
        "entry": entry,
        "target_1": t1,
        "target_2": t2,
        "stop_loss": sl,
        "vwap": vwap,
        "rsi": rsi_14,
        "ema_9": ema_9,
        "ema_21": ema_21,
        "atr": atr,
        "sparkline": sparkline,
        "reasons": reasons
    }
