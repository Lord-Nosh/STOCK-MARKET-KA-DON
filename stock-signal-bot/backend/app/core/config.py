from typing import List, Dict

# Liquid Nifty 50 / F&O constituent universe
# Note: Tata Motors demerged into commercial/passenger (TMPV.NS) and Zomato transitioned to ETERNAL.NS on NSE
TRACKED_UNIVERSE: List[Dict[str, str]] = [
    {"symbol": "RELIANCE", "ticker": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy / Retail", "groww": "reliance-industries"},
    {"symbol": "TCS", "ticker": "TCS.NS", "name": "Tata Consultancy Services", "sector": "IT", "groww": "tata-consultancy-services"},
    {"symbol": "HDFCBANK", "ticker": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking", "groww": "hdfc-bank"},
    {"symbol": "INFY", "ticker": "INFY.NS", "name": "Infosys", "sector": "IT", "groww": "infosys"},
    {"symbol": "ICICIBANK", "ticker": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking", "groww": "icici-bank"},
    {"symbol": "SBIN", "ticker": "SBIN.NS", "name": "State Bank of India", "sector": "PSU Bank", "groww": "state-bank-of-india"},
    {"symbol": "BHARTIARTL", "ticker": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecom", "groww": "bharti-airtel"},
    {"symbol": "TMPV", "ticker": "TMPV.NS", "name": "Tata Motors Passenger", "sector": "Auto / EV", "groww": "tata-motors"},
    {"symbol": "ITC", "ticker": "ITC.NS", "name": "ITC Ltd", "sector": "FMCG", "groww": "itc"},
    {"symbol": "LT", "ticker": "LT.NS", "name": "Larsen & Toubro", "sector": "Capital Goods", "groww": "larsen-and-toubro"},
    {"symbol": "KOTAKBANK", "ticker": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "Banking", "groww": "kotak-mahindra-bank"},
    {"symbol": "BAJFINANCE", "ticker": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "NBFC", "groww": "bajaj-finance"},
    {"symbol": "ADANIENT", "ticker": "ADANIENT.NS", "name": "Adani Enterprises", "sector": "Metals / Mining", "groww": "adani-enterprises"},
    {"symbol": "SUNPHARMA", "ticker": "SUNPHARMA.NS", "name": "Sun Pharma", "sector": "Pharma", "groww": "sun-pharmaceutical-industries"},
    {"symbol": "ETERNAL", "ticker": "ETERNAL.NS", "name": "Eternal (Zomato)", "sector": "Consumer Internet", "groww": "zomato"},
    {"symbol": "TATASTEEL", "ticker": "TATASTEEL.NS", "name": "Tata Steel", "sector": "Metals", "groww": "tata-steel"},
]

# Risk Engine Constraints (Configurable for user's ₹18,000 capital)
ACCOUNT_CAPITAL = 18000.0          # Base capital in INR
RISK_PER_TRADE_PCT = 0.005         # 0.5% risk per trade = ₹90
MAX_DAILY_LOSS_PCT = 0.015         # 1.5% max daily loss = ₹270
MIN_RISK_REWARD_RATIO = 2.0        # Mandatory 1:2 minimum Risk-to-Reward
MIN_CONFLUENCE_SCORE = 7           # Confluence threshold for BUY/SELL Candidate (out of 10)
SWING_PROFIT_TARGET_PCT = 0.08     # 8% target for delivery swings
