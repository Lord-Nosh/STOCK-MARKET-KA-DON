from typing import Dict, Any
from app.indicators.calculations import calculate_trade_risk_and_sizing
from app.core.config import MIN_CONFLUENCE_SCORE, ACCOUNT_CAPITAL

class SignalRiskDepartment:
    """
    DEPARTMENT 5: SIGNAL & RISK ENGINE
    Responsibility: Takes unified inputs from Market Data, Technical Analysis,
    Fundamental Analysis, and Market Intelligence, then produces:
    - Final BUY / SELL / WAIT verdict (7-10 confluence score)
    - Precise Entry, Stop Loss, Target 1, Target 2
    - Strict position size (0.5% risk = ₹90 on ₹18,000 capital)
    - Explainable reasons detailing every factor.
    """
    def synthesize_decision(
        self,
        market_data: Dict[str, Any],
        technicals: Dict[str, Any],
        fundamentals: Dict[str, Any],
        intelligence: Dict[str, Any],
        capital: float = ACCOUNT_CAPITAL
    ) -> Dict[str, Any]:
        c_price = market_data["current_price"]
        struct = technicals.get("market_structure", {})
        zones = technicals.get("supply_demand", {})
        key_candle = technicals.get("key_candle", {})
        vwap = technicals.get("vwap", c_price)
        ema_9 = technicals.get("ema_9", c_price)
        ema_21 = technicals.get("ema_21", c_price)
        rsi = technicals.get("rsi", 50.0)
        adx = technicals.get("adx", 20.0)
        p_di = technicals.get("plus_di", 20.0)
        m_di = technicals.get("minus_di", 20.0)
        rvol = technicals.get("rvol", 1.0)
        atr = technicals.get("atr", 5.0)

        bull_score = 0
        bear_score = 0
        bull_reasons = []
        bear_reasons = []

        # 1. Market Structure (+2)
        if "BULLISH" in struct.get("trend", "") or struct.get("bos") and c_price > struct.get("last_swing_low", 0):
            bull_score += 2
            bull_reasons.append(f"Market Structure (+2): {struct.get('description')}")
        elif "BEARISH" in struct.get("trend", "") or struct.get("bos") and c_price < struct.get("last_swing_high", 0):
            bear_score += 2
            bear_reasons.append(f"Market Structure (+2): {struct.get('description')}")

        # 2. Supply / Demand Zone (+2)
        if zones.get("at_demand") or key_candle.get("is_bullish") and zones.get("demand_zone"):
            bull_score += 2
            bull_reasons.append(f"Supply/Demand (+2): Price respecting Demand Base ₹{zones['demand_zone']['bottom']}-₹{zones['demand_zone']['top']}")
        elif zones.get("at_supply") or key_candle.get("is_bearish") and zones.get("supply_zone"):
            bear_score += 2
            bear_reasons.append(f"Supply/Demand (+2): Price rejecting Supply Base ₹{zones['supply_zone']['bottom']}-₹{zones['supply_zone']['top']}")

        # 3. VWAP Alignment (+2)
        if c_price > vwap:
            bull_score += 2
            bull_reasons.append(f"VWAP Alignment (+2): Price (₹{c_price}) holds strictly above institutional VWAP (₹{vwap})")
        else:
            bear_score += 2
            bear_reasons.append(f"VWAP Alignment (+2): Price (₹{c_price}) rejected below institutional VWAP (₹{vwap})")

        # 4. EMA 9/21 (+1)
        if ema_9 > ema_21 and c_price >= ema_9:
            bull_score += 1
            bull_reasons.append(f"EMA 9/21 (+1): 9-EMA (₹{ema_9}) expansion above 21-EMA (₹{ema_21})")
        elif ema_9 < ema_21 and c_price <= ema_9:
            bear_score += 1
            bear_reasons.append(f"EMA 9/21 (+1): 9-EMA (₹{ema_9}) downward slope under 21-EMA (₹{ema_21})")

        # 5. Relative Volume (+1)
        if rvol >= 1.25:
            if c_price >= ema_9:
                bull_score += 1
                bull_reasons.append(f"Volume (+1): RVOL at {rvol}x average institutional turnover")
            else:
                bear_score += 1
                bear_reasons.append(f"Volume (+1): RVOL distribution at {rvol}x average")

        # 6. Momentum RSI + ADX (+1)
        if 52 <= rsi <= 68 and adx >= 20 and p_di > m_di:
            bull_score += 1
            bull_reasons.append(f"Momentum (+1): RSI ({rsi}) in expansion zone with ADX trend ({adx})")
        elif 32 <= rsi <= 48 and adx >= 20 and m_di > p_di:
            bear_score += 1
            bear_reasons.append(f"Momentum (+1): RSI ({rsi}) bearish pressure with ADX ({adx})")

        # 7. Market Intelligence Sector / Macro (+1)
        nifty_trend = intelligence.get("nifty_50", {}).get("trend", "SIDEWAYS")
        if nifty_trend == "BULLISH":
            bull_score += 1
            bull_reasons.append("Market Intelligence (+1): Nifty 50 macro trend is positive")
        elif nifty_trend == "BEARISH":
            bear_score += 1
            bear_reasons.append("Market Intelligence (+1): Nifty 50 macro trend is negative")

        # Fundamental Risk Filter: Block high debt or severe quality traps
        if not fundamentals.get("quality_filter_passed", True):
            bull_score = min(bull_score, 4)
            bull_reasons.append("Fundamental Filter Warning: High balance sheet debt detected; longs capped")

        # Session Trap Filter (09:15-09:30 AM block)
        if intelligence.get("session", {}).get("phase") == "OPENING_TRAP_ZONE":
            return {
                "signal": "WAIT",
                "confluence_score": 0,
                "confidence": 30,
                "entry": c_price, "target_1": c_price, "target_2": c_price, "stop_loss": c_price,
                "reasons": ["Opening Trap Zone Active (09:15-09:30 AM): Orders blocked to prevent stop-loss hunting."],
                "risk_sizing": calculate_trade_risk_and_sizing(c_price, c_price - 1.0, c_price + 2.0, c_price + 3.0, capital)
            }

        # Final Verdict Decision
        volatility_buffer = max(1.2 * atr, c_price * 0.005)

        if bull_score >= bear_score and bull_score >= MIN_CONFLUENCE_SCORE:
            signal_state = "BUY CANDIDATE"
            total_score = bull_score
            reasons = bull_reasons
            stop_loss = round(c_price - volatility_buffer, 2)
            target_1 = round(c_price + (volatility_buffer * 2.0), 2)  # Mandatory 1:2 R:R
            target_2 = round(c_price + (volatility_buffer * 3.0), 2)
        elif bear_score > bull_score and bear_score >= MIN_CONFLUENCE_SCORE:
            signal_state = "SELL CANDIDATE"
            total_score = bear_score
            reasons = bear_reasons
            stop_loss = round(c_price + volatility_buffer, 2)
            target_1 = round(c_price - (volatility_buffer * 2.0), 2)  # Mandatory 1:2 R:R
            target_2 = round(c_price - (volatility_buffer * 3.0), 2)
        else:
            signal_state = "WATCHING" if bear_score >= 4 or bull_score >= 4 else "SCANNING"
            total_score = max(bull_score, bear_score)
            reasons = ["Confluence score below trigger threshold (7/10 required). Awaiting clean setup alignment."]
            # If bearish bias is dominant or equal in a short scanner, ensure short levels are mathematically correct
            if bear_score >= bull_score:
                stop_loss = round(c_price + volatility_buffer, 2)   # Short stop is strictly ABOVE entry
                target_1 = round(c_price - (volatility_buffer * 2.0), 2)  # Short target is strictly BELOW entry
                target_2 = round(c_price - (volatility_buffer * 3.0), 2)
            else:
                stop_loss = round(c_price - volatility_buffer, 2)
                target_1 = round(c_price + (volatility_buffer * 2.0), 2)
                target_2 = round(c_price + (volatility_buffer * 3.0), 2)

        risk_profile = calculate_trade_risk_and_sizing(
            entry_price=c_price,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            capital=capital
        )

        # A high confluence score is not enough: block candidate signals when
        # sizing violates the defined risk budget or the minimum reward ratio.
        if signal_state in {"BUY CANDIDATE", "SELL CANDIDATE"} and not risk_profile.get("trade_allowed", False):
            signal_state = "WAIT"
            reasons = list(reasons) + [
                "Risk guard blocked this candidate: "
                + str(risk_profile.get("rejection_reason") or "POSITION_SIZE_NOT_ALLOWED")
            ]

        return {
            "signal": signal_state,
            "confluence_score": total_score,
            "max_score": 10,
            "confidence": min(95, max(45, total_score * 10)),
            "entry": c_price,
            "target_1": target_1,
            "target_2": target_2,
            "stop_loss": stop_loss,
            "reasons": reasons,
            "risk_sizing": risk_profile
        }

signal_risk_dep = SignalRiskDepartment()
