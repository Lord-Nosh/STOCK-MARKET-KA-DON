import math
from typing import Dict, Any, List

class SystemOneDecisionModel:
    """
    Sub-millisecond System 1 fast-reflex inference engine.
    Applies multi-factor probabilistic scoring across:
    1. Trend & VWAP Slope Confluence
    2. Momentum Exhaustion Penalty (Overbought/Oversold Dampener)
    3. Volatility Compression / Expansion (ATR ratio)
    4. Sentiment Alignment Weighting
    """
    
    def evaluate(
        self,
        symbol: str,
        price: float,
        vwap: float,
        rsi: float,
        ema_9: float,
        ema_21: float,
        atr: float,
        change_pct: float,
        news_sentiment: str,
        market_phase: str
    ) -> Dict[str, Any]:
        score = 0.50  # 0.00 (Heavy Sell) to 1.00 (Strong Buy)
        rules_fired = []
        
        # 1. VWAP Distance & Institutional Acceptance
        vwap_delta_pct = ((price - vwap) / vwap) * 100 if vwap else 0
        if vwap_delta_pct > 0.15:
            score += 0.15
            rules_fired.append("Price holds firmly above institutional VWAP floor")
        elif vwap_delta_pct < -0.15:
            score -= 0.15
            rules_fired.append("Price rejected below institutional VWAP ceiling")
            
        # 2. Dual EMA Exponential Gradient
        ema_spread = ((ema_9 - ema_21) / ema_21) * 100 if ema_21 else 0
        if ema_spread > 0.1:
            score += 0.12
            rules_fired.append("Short-term 9-EMA velocity accelerating above 21-EMA")
        elif ema_spread < -0.1:
            score -= 0.12
            rules_fired.append("Short-term 9-EMA slope dipping under 21-EMA")
            
        # 3. Non-Linear RSI Momentum Scoring
        # Optimal bullish sweet spot: 55 to 68. Overbought penalty > 74.
        if 55 <= rsi <= 68:
            score += 0.12
            rules_fired.append(f"RSI ({rsi}) in high-velocity expansion sweet spot")
        elif rsi > 74:
            score -= 0.18
            rules_fired.append(f"RSI ({rsi}) stretched into extreme overbought trap risk")
        elif 30 <= rsi <= 45:
            score -= 0.10
            rules_fired.append(f"RSI ({rsi}) under bearish pressure")
        elif rsi < 25:
            score += 0.10  # Potential mean-reversion scalp
            rules_fired.append(f"RSI ({rsi}) oversold; mean reversion bounce potential")
            
        # 4. News Sentiment Alignment
        if news_sentiment == "BULLISH":
            score += 0.08
            rules_fired.append("Positive headline sentiment aligning with technicals")
        elif news_sentiment == "BEARISH":
            score -= 0.08
            rules_fired.append("Risk Warning: Negative press headlines exerting selling pressure")
            
        # 5. Timing Window Penalty
        if market_phase == "OPENING_TRAP_ZONE":
            score = 0.50  # Hard neutralize during 09:15-09:30 AM
            rules_fired.append("Session Rule: High-spread opening traps active; signals neutralized")
            
        # Clamp score between 0.05 and 0.95
        score = round(max(0.05, min(0.95, score)), 2)
        
        # Determine AI Verdict
        if score >= 0.72:
            verdict = "STRONG_BUY_CONFLUENCE"
            action = "HIGH PROBABILITY LONG"
        elif score >= 0.58:
            verdict = "MODERATE_BUY"
            action = "WATCH FOR PULLBACK TO VWAP"
        elif score <= 0.32:
            verdict = "STRONG_SELL_CONFLUENCE"
            action = "HIGH PROBABILITY SHORT"
        elif score <= 0.44:
            verdict = "MODERATE_SELL"
            action = "WATCH FOR BREAKDOWN"
        else:
            verdict = "CHOP_NEUTRAL"
            action = "NO EDGE / WAIT"
            
        return {
            "ai_score": score,
            "ai_verdict": verdict,
            "recommended_action": action,
            "system_one_rules": rules_fired
        }

decision_engine = SystemOneDecisionModel()
