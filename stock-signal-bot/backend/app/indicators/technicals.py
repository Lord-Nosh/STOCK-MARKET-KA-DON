from typing import List

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Computes Relative Strength Index on confirmed closes"""
    if len(prices) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        gains.append(delta if delta >= 0 else 0.0)
        losses.append(abs(delta) if delta < 0 else 0.0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)

def calculate_ema(prices: List[float], span: int) -> float:
    """Computes Exponential Moving Average"""
    if not prices:
        return 0.0
    if len(prices) < span:
        return prices[-1]
    multiplier = 2.0 / (span + 1.0)
    ema = prices[0]
    for p in prices[1:]:
        ema = (p - ema) * multiplier + ema
    return round(ema, 2)

def calculate_vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> float:
    """Computes Volume Weighted Average Price (VWAP)"""
    cum_pv, cum_vol = 0.0, 0.0
    for h, l, c, v in zip(highs, lows, closes, volumes):
        if v and h and l and c:
            cum_pv += ((h + l + c) / 3.0) * v
            cum_vol += v
    if cum_vol == 0:
        return closes[-1] if closes else 0.0
    return round(cum_pv / cum_vol, 2)

def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Computes Average True Range for dynamic volatility stop-loss"""
    if len(closes) < 2:
        return 1.0
    tr_list = []
    for i in range(1, len(closes)):
        h, l, prev_c = highs[i], lows[i], closes[i - 1]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)
    recent_tr = tr_list[-period:] if len(tr_list) >= period else tr_list
    return round(sum(recent_tr) / len(recent_tr), 2) if recent_tr else 1.0
