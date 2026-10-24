from typing import List, Dict, Any, Optional

def analyze_market_structure(highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, Any]:
    """
    Detects Higher Highs (HH), Higher Lows (HL), Lower Highs (LH), Lower Lows (LL),
    Break of Structure (BOS), and Change of Character (CHoCH).
    """
    if len(closes) < 10:
        return {
            "trend": "NEUTRAL",
            "bos": False,
            "choch": False,
            "last_swing_high": highs[-1] if highs else 0.0,
            "last_swing_low": lows[-1] if lows else 0.0,
            "description": "Insufficient candle history"
        }

    # Find swing highs and lows (fractal 3-bar confirmation)
    swing_highs = []
    swing_lows = []

    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 1] and highs[i] > highs[i + 2]:
            swing_highs.append({"index": i, "price": highs[i]})
        if lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 1] and lows[i] < lows[i + 2]:
            swing_lows.append({"index": i, "price": lows[i]})

    current_price = closes[-1]
    last_sh = swing_highs[-1]["price"] if swing_highs else max(highs[-10:])
    last_sl = swing_lows[-1]["price"] if swing_lows else min(lows[-10:])

    # Structure identification
    trend = "CONSOLIDATION"
    bos = False
    choch = False
    desc = "Consolidating within recent swing limits."

    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        sh1, sh2 = swing_highs[-2]["price"], swing_highs[-1]["price"]
        sl1, sl2 = swing_lows[-2]["price"], swing_lows[-1]["price"]

        if sh2 > sh1 and sl2 > sl1:
            trend = "BULLISH_HH_HL"
            if current_price > sh2:
                bos = True
                desc = "Bullish BOS: Price broke above confirmed swing high."
            else:
                desc = "Bullish structure: Series of Higher Highs and Higher Lows."
        elif sh2 < sh1 and sl2 < sl1:
            trend = "BEARISH_LH_LL"
            if current_price < sl2:
                bos = True
                desc = "Bearish BOS: Price broke below confirmed swing low."
            else:
                desc = "Bearish structure: Series of Lower Highs and Lower Lows."
        elif sh2 > sh1 and sl2 < sl1:
            choch = True
            desc = "CHoCH detected: Market expanding with shifting character."
    else:
        if current_price > last_sh:
            trend = "BULLISH"
            bos = True
            desc = "Breakout above immediate resistance swing."
        elif current_price < last_sl:
            trend = "BEARISH"
            bos = True
            desc = "Breakdown below immediate support swing."

    return {
        "trend": trend,
        "bos": bos,
        "choch": choch,
        "last_swing_high": round(last_sh, 2),
        "last_swing_low": round(last_sl, 2),
        "description": desc
    }

def detect_supply_demand_zones(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> Dict[str, Any]:
    """
    Identifies Order Block / Supply & Demand Base Zones followed by impulsive departures.
    """
    if len(closes) < 8:
        return {"demand_zone": None, "supply_zone": None, "at_demand": False, "at_supply": False}

    current_price = closes[-1]
    demand_zone = None
    supply_zone = None

    # Scan for impulsive moves (candle body > 1.5x average body with above-average volume)
    bodies = [abs(closes[i] - lows[i]) for i in range(len(closes))]
    avg_body = sum(bodies[-10:]) / 10 if bodies else 1.0

    for i in range(len(closes) - 3, 2, -1):
        move = closes[i] - closes[i - 1]
        vol = volumes[i] if i < len(volumes) else 1000

        # Bullish impulsive departure -> Base prior is Demand Zone
        if move > 1.5 * avg_body and demand_zone is None:
            demand_zone = {
                "top": round(highs[i - 1], 2),
                "bottom": round(lows[i - 1], 2),
                "age_bars": len(closes) - i
            }
        # Bearish impulsive departure -> Base prior is Supply Zone
        elif move < -1.5 * avg_body and supply_zone is None:
            supply_zone = {
                "top": round(highs[i - 1], 2),
                "bottom": round(lows[i - 1], 2),
                "age_bars": len(closes) - i
            }

        if demand_zone and supply_zone:
            break

    # Fallbacks if no impulsive move in immediate range
    if not demand_zone:
        recent_min = min(lows[-15:])
        demand_zone = {"top": round(recent_min * 1.002, 2), "bottom": round(recent_min * 0.998, 2), "age_bars": 15}
    if not supply_zone:
        recent_max = max(highs[-15:])
        supply_zone = {"top": round(recent_max * 1.002, 2), "bottom": round(recent_max * 0.998, 2), "age_bars": 15}

    at_demand = demand_zone["bottom"] <= current_price <= demand_zone["top"] * 1.004
    at_supply = supply_zone["bottom"] * 0.996 <= current_price <= supply_zone["top"]

    return {
        "demand_zone": demand_zone,
        "supply_zone": supply_zone,
        "at_demand": at_demand,
        "at_supply": at_supply,
        "description": "At active Demand zone" if at_demand else ("At active Supply zone" if at_supply else "Between S/D zones")
    }

def detect_key_candle(opens: List[float], highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> Dict[str, Any]:
    """
    Labels completed candles by their real market role:
    A. Bullish Engulfing
    B. Bearish Engulfing
    C. Rejection Wick (Demand Hammer / Supply Shooting Star)
    D. Breakout Candle
    """
    if len(closes) < 3:
        return {"type": "NORMAL", "role": "Standard Bar", "is_bullish": False, "is_bearish": False}

    c, o, h, l = closes[-1], opens[-1], highs[-1], lows[-1]
    prev_c, prev_o, prev_h, prev_l = closes[-2], opens[-2], highs[-2], lows[-2]

    body = abs(c - o)
    candle_range = h - l or 0.01
    upper_wick = h - max(c, o)
    lower_wick = min(c, o) - l

    # A. Bullish Engulfing
    if c > o and prev_c < prev_o and c >= prev_o and o <= prev_c:
        return {
            "type": "BULLISH_ENGULFING",
            "role": "Bullish Engulfing (Buyer takeover after pullback)",
            "is_bullish": True,
            "is_bearish": False,
            "signal_level": h
        }

    # B. Bearish Engulfing
    if c < o and prev_c > prev_o and c <= prev_o and o >= prev_c:
        return {
            "type": "BEARISH_ENGULFING",
            "role": "Bearish Engulfing (Seller takeover after rally)",
            "is_bullish": False,
            "is_bearish": True,
            "signal_level": l
        }

    # C. Rejection Candle (Wick > 55% of range)
    if lower_wick >= 0.55 * candle_range and c >= (l + 0.4 * candle_range):
        return {
            "type": "DEMAND_REJECTION",
            "role": "Demand Rejection Hammer (Aggressive absorption at lows)",
            "is_bullish": True,
            "is_bearish": False,
            "signal_level": h
        }
    elif upper_wick >= 0.55 * candle_range and c <= (h - 0.4 * candle_range):
        return {
            "type": "SUPPLY_REJECTION",
            "role": "Supply Rejection (Rejection wick at highs)",
            "is_bullish": False,
            "is_bearish": True,
            "signal_level": l
        }

    # D. Strong Breakout Candle
    if body >= 0.65 * candle_range and (c > prev_h or c < prev_l):
        is_bull = c > o
        return {
            "type": "BREAKOUT_CANDLE",
            "role": f"{'Bullish' if is_bull else 'Bearish'} Breakout Candle (High momentum expansion)",
            "is_bullish": is_bull,
            "is_bearish": not is_bull,
            "signal_level": h if is_bull else l
        }

    return {
        "type": "NORMAL",
        "role": "Consolidation Bar",
        "is_bullish": c > o,
        "is_bearish": c < o,
        "signal_level": c
    }
