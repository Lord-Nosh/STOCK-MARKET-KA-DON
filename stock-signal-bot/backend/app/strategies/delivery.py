from typing import List, Dict, Any
from app.indicators.technicals import calculate_rsi, calculate_ema
from app.core.config import SWING_PROFIT_TARGET_PCT

def evaluate_delivery_signal(current_price: float, daily_closes: List[float]) -> Dict[str, Any]:
    """Evaluates multi-week positional trend (20 & 50 Daily EMAs)"""
    ema_20 = calculate_ema(daily_closes, 20) if len(daily_closes) >= 20 else current_price
    ema_50 = calculate_ema(daily_closes, 50) if len(daily_closes) >= 50 else current_price
    rsi_14 = calculate_rsi(daily_closes, 14) if len(daily_closes) >= 15 else 50.0

    reasons: List[str] = []
    if current_price > ema_20 and ema_20 > ema_50:
        signal_type = "STRONG BUY (Multi-Week Trend)"
        confidence = 85
        reasons.append(f"Golden Trend: 20-Day EMA (₹{ema_20}) above 50-Day EMA (₹{ema_50})")
        reasons.append("Trading consistently above major institutional accumulation base")
    elif current_price < ema_50:
        signal_type = "AVOID / WAIT (Downtrend)"
        confidence = 70
        reasons.append(f"Price below 50-Day baseline (₹{ema_50})")
    else:
        signal_type = "ACCUMULATE / HOLD"
        confidence = 60
        reasons.append(f"Consolidation range. Support defined near ₹{ema_50}")

    target = round(current_price * (1 + SWING_PROFIT_TARGET_PCT), 2)
    sl = round(ema_50 * 0.97, 2)

    return {
        "signal": signal_type,
        "confidence": confidence,
        "target": target,
        "stop_loss": sl,
        "ema_20": ema_20,
        "ema_50": ema_50,
        "rsi": rsi_14,
        "reasons": reasons
    }
