from typing import Dict, Any, List
from app.indicators.technicals import (
    calculate_rsi, calculate_ema, calculate_vwap,
    calculate_atr, calculate_adx_di, calculate_rvol
)
from app.indicators.structure import (
    analyze_market_structure, detect_supply_demand_zones, detect_key_candle
)

class TechnicalAnalysisDepartment:
    """
    DEPARTMENT 2: TECHNICAL ANALYSIS
    Responsibility: Evaluates purely mathematical and price-action structures:
    VWAP, EMA, RSI, ADX, Fibonacci, Key Candles, and Supply/Demand zones.
    """
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        c_5m = market_data.get("candles_5m", {})
        opens = c_5m.get("opens", [])
        highs = c_5m.get("highs", [])
        lows = c_5m.get("lows", [])
        closes = c_5m.get("closes", [])
        volumes = c_5m.get("volumes", [])

        c_price = market_data["current_price"]

        if len(closes) < 10:
            return {
                "rsi": 50.0, "ema_9": c_price, "ema_21": c_price, "vwap": c_price,
                "atr": 5.0, "adx": 20.0, "rvol": 1.0,
                "market_structure": {"trend": "NEUTRAL", "description": "Insufficient bars"},
                "supply_demand": {"description": "Awaiting candle bars"},
                "key_candle": {"role": "Normal Bar", "is_bullish": False, "is_bearish": False},
                "sparkline": [c_price] * 10,
                "fibonacci": {"pocket_min": c_price, "pocket_max": c_price}
            }

        rsi = calculate_rsi(closes, 14)
        ema_9 = calculate_ema(closes, 9)
        ema_21 = calculate_ema(closes, 21)
        vwap = calculate_vwap(highs, lows, closes, volumes)
        atr = calculate_atr(highs, lows, closes, 14)
        adx, p_di, m_di = calculate_adx_di(highs, lows, closes, 14)
        rvol = calculate_rvol(volumes, 20)

        struct = analyze_market_structure(highs, lows, closes)
        zones = detect_supply_demand_zones(highs, lows, closes, volumes)
        key_candle = detect_key_candle(opens, highs, lows, closes, volumes)

        sh = struct["last_swing_high"]
        sl = struct["last_swing_low"]
        fib_range = sh - sl or 1.0
        fib_pocket_min = round(sl + 0.500 * fib_range, 2)
        fib_pocket_max = round(sl + 0.618 * fib_range, 2)

        sparkline = [round(c, 2) for c in closes[-20:]]

        return {
            "rsi": rsi,
            "ema_9": ema_9,
            "ema_21": ema_21,
            "vwap": vwap,
            "atr": atr,
            "adx": adx,
            "plus_di": p_di,
            "minus_di": m_di,
            "rvol": rvol,
            "market_structure": struct,
            "supply_demand": zones,
            "key_candle": key_candle,
            "sparkline": sparkline,
            "fibonacci": {
                "swing_high": sh,
                "swing_low": sl,
                "golden_pocket": f"₹{fib_pocket_min} - ₹{fib_pocket_max}"
            }
        }

technical_dep = TechnicalAnalysisDepartment()
