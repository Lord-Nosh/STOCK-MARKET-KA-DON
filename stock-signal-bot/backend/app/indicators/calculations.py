from typing import Tuple

def compute_intraday_levels(price: float, atr: float, signal_type: str) -> Tuple[float, float, float, float]:
    """
    Computes (Entry, Target 1, Target 2, Stop Loss).
    Enforces minimum 0.7% movement to defeat STT/brokerage friction.
    """
    risk = max(atr * 1.5, price * 0.007)
    target_1_dist = risk * 1.5
    target_2_dist = risk * 2.5

    if "BUY" in signal_type:
        entry = round(price, 2)
        sl = round(price - risk, 2)
        t1 = round(price + target_1_dist, 2)
        t2 = round(price + target_2_dist, 2)
    elif "SELL" in signal_type or "SHORT" in signal_type:
        entry = round(price, 2)
        sl = round(price + risk, 2)
        t1 = round(price - target_1_dist, 2)
        t2 = round(price - target_2_dist, 2)
    else:
        entry = round(price, 2)
        sl = round(price * 0.993, 2)
        t1 = round(price * 1.010, 2)
        t2 = round(price * 1.020, 2)

    return entry, t1, t2, sl
