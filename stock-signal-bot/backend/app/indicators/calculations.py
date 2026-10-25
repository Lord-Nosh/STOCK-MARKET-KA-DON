import math
from typing import Dict, Any, Tuple
from app.core.config import ACCOUNT_CAPITAL, RISK_PER_TRADE_PCT, MIN_RISK_REWARD_RATIO


def compute_intraday_levels(price: float, atr: float, signal_type: str) -> Tuple[float, float, float, float]:
    """Compute (Entry, Target 1, Target 2, Stop Loss)."""
    if not math.isfinite(price) or price <= 0:
        raise ValueError("price must be a finite positive number")
    if not math.isfinite(atr) or atr < 0:
        raise ValueError("atr must be a finite non-negative number")

    risk = max(atr * 1.5, price * 0.005)
    t1_dist = risk * 2.0
    t2_dist = risk * 3.0

    if "BUY" in signal_type:
        entry, sl = round(price, 2), round(price - risk, 2)
        t1, t2 = round(price + t1_dist, 2), round(price + t2_dist, 2)
    elif "SELL" in signal_type or "SHORT" in signal_type:
        entry, sl = round(price, 2), round(price + risk, 2)
        t1, t2 = round(price - t1_dist, 2), round(price - t2_dist, 2)
    else:
        entry, sl = round(price, 2), round(price - risk, 2)
        t1, t2 = round(price + t1_dist, 2), round(price + t2_dist, 2)
    return entry, t1, t2, sl


def calculate_trade_risk_and_sizing(
    entry_price: float,
    stop_loss: float,
    target_1: float,
    target_2: float,
    capital: float = ACCOUNT_CAPITAL,
) -> Dict[str, Any]:
    """
    Conservative estimated equity sizing. Returns zero shares whenever a
    whole share would breach the defined risk budget or capital constraint.
    Broker-specific margin and fee models must be verified before live use.
    """
    values = (entry_price, stop_loss, target_1, target_2, capital)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("prices and capital must be finite numbers")
    if capital <= 0:
        raise ValueError("capital must be greater than zero")
    if any(v <= 0 for v in values[:4]):
        raise ValueError("entry, stop-loss, and targets must be positive prices")

    allowable_risk_inr = round(capital * RISK_PER_TRADE_PCT, 2)
    risk_distance = abs(entry_price - stop_loss)
    reward_distance_t1 = abs(target_1 - entry_price)

    if risk_distance <= 0:
        return {
            "capital_allocated": capital, "allowable_risk_inr": allowable_risk_inr,
            "actual_risk_inr": 0.0, "shares_qty": 0, "trade_value": 0.0,
            "margin_required": 0.0, "risk_distance_pts": 0.0,
            "reward_distance_pts": round(reward_distance_t1, 2),
            "risk_reward_ratio": "1:0.0", "passes_rr_filter": False,
            "estimated_friction_inr": 0.0, "expected_net_t1_inr": 0.0,
            "trade_allowed": False, "rejection_reason": "INVALID_STOP_DISTANCE",
        }

    raw_shares = math.floor(allowable_risk_inr / risk_distance)
    # Existing model's 5x leverage convention is only an approximation.
    capital_limited_shares = math.floor((capital * 5.0) / entry_price)
    shares = max(0, min(raw_shares, capital_limited_shares))
    trade_value = round(shares * entry_price, 2)
    margin_required = round(trade_value / 5.0, 2)
    actual_risk_inr = round(shares * risk_distance, 2)
    rr_value = reward_distance_t1 / risk_distance
    rr_ratio = round(rr_value, 2)
    passes_rr_filter = rr_value >= MIN_RISK_REWARD_RATIO

    brokerage = min(20.0, trade_value * 0.0005) * 2 if shares else 0.0
    stt = round(trade_value * 0.00025, 2) if shares else 0.0
    exchange_fee = round(trade_value * 2 * 0.0000345, 2) if shares else 0.0
    gst = round((brokerage + exchange_fee) * 0.18, 2)
    total_friction_inr = round(brokerage + stt + exchange_fee + gst, 2)
    net_t1_gain = round((reward_distance_t1 * shares) - total_friction_inr, 2)

    rejection_reason = None
    if shares == 0:
        rejection_reason = "RISK_BUDGET_OR_CAPITAL_TOO_SMALL_FOR_ONE_SHARE"
    elif not passes_rr_filter:
        rejection_reason = "MINIMUM_RISK_REWARD_NOT_MET"

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
        "expected_net_t1_inr": net_t1_gain,
        "trade_allowed": shares > 0 and passes_rr_filter and actual_risk_inr <= allowable_risk_inr,
        "rejection_reason": rejection_reason,
    }
