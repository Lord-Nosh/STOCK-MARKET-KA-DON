import math
from typing import Dict, Any, Tuple
from app.core.config import ACCOUNT_CAPITAL, RISK_PER_TRADE_PCT, MIN_RISK_REWARD_RATIO

def compute_intraday_levels(price: float, atr: float, signal_type: str) -> Tuple[float, float, float, float]:
    """
    Computes (Entry, Target 1, Target 2, Stop Loss).
    Enforces minimum 1:2 Risk-Reward ratio.
    """
    risk = max(atr * 1.5, price * 0.005)
    t1_dist = risk * 2.0
    t2_dist = risk * 3.0

    if "BUY" in signal_type:
        entry = round(price, 2)
        sl = round(price - risk, 2)
        t1 = round(price + t1_dist, 2)
        t2 = round(price + t2_dist, 2)
    elif "SELL" in signal_type or "SHORT" in signal_type:
        entry = round(price, 2)
        sl = round(price + risk, 2)
        t1 = round(price - t1_dist, 2)
        t2 = round(price - t2_dist, 2)
    else:
        entry = round(price, 2)
        sl = round(price - risk, 2)
        t1 = round(price + t1_dist, 2)
        t2 = round(price + t2_dist, 2)

    return entry, t1, t2, sl

def calculate_trade_risk_and_sizing(
    entry_price: float,
    stop_loss: float,
    target_1: float,
    target_2: float,
    capital: float = ACCOUNT_CAPITAL
) -> Dict[str, Any]:
    """
    Mandatory Risk Engine:
    - 0.5% risk per trade = ₹90 on ₹18,000 capital
    - Position Size = ₹90 ÷ per-share risk distance (rounded down to whole shares)
    - Enforces 1:2 Minimum Risk-to-Reward Ratio
    - Computes estimated STT, Exchange Turnover, GST, and SEBI charges
    """
    risk_distance = abs(entry_price - stop_loss)
    reward_distance_t1 = abs(target_1 - entry_price)

    if risk_distance <= 0:
        risk_distance = max(entry_price * 0.005, 1.0)

    allowable_risk_inr = round(capital * RISK_PER_TRADE_PCT, 2)  # ₹90 on ₹18k
    raw_shares = allowable_risk_inr / risk_distance
    shares = max(1, math.floor(raw_shares))

    trade_value = round(shares * entry_price, 2)
    margin_required = round(trade_value / 5.0, 2)

    if margin_required > capital:
        shares = max(1, math.floor((capital * 5.0) / entry_price))
        trade_value = round(shares * entry_price, 2)
        margin_required = round(trade_value / 5.0, 2)

    actual_risk_inr = round(shares * risk_distance, 2)
    rr_ratio = round(reward_distance_t1 / risk_distance, 2) if risk_distance > 0 else 1.0
    passes_rr_filter = rr_ratio >= MIN_RISK_REWARD_RATIO

    brokerage = min(20.0, trade_value * 0.0005) * 2
    stt = round(trade_value * 0.00025, 2)
    exchange_fee = round(trade_value * 2 * 0.0000345, 2)
    gst = round((brokerage + exchange_fee) * 0.18, 2)
    total_friction_inr = round(brokerage + stt + exchange_fee + gst, 2)
    net_t1_gain = round((reward_distance_t1 * shares) - total_friction_inr, 2)

    return {
        "capital_allocated": capital,
        "allowable_risk_inr": allowable_risk_inr,
        "actual_risk_inr": actual_risk_inr,
        "shares_qty": shares,
        "trade_value": trade_value,
        "margin_required": margin_required,
        "risk_distance_pts": round(risk_distance, 2),
        "reward_distance_pts": round(reward_distance_t1, 2),
        "risk_reward_ratio": f"1:{rr_ratio}",
        "passes_rr_filter": passes_rr_filter,
        "estimated_friction_inr": total_friction_inr,
        "expected_net_t1_inr": net_t1_gain
    }
