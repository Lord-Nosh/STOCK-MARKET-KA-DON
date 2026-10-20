from typing import List, Dict

# Liquid Nifty 50 / Nifty 100 constituents eligible for F&O and high-turnover intraday
TRACKED_UNIVERSE: List[Dict[str, str]] = [
    {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy / Retail", "groww": "reliance-industries"},
    {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT", "groww": "tata-consultancy-services"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking", "groww": "hdfc-bank"},
    {"symbol": "INFY", "name": "Infosys", "sector": "IT", "groww": "infosys"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "Banking", "groww": "icici-bank"},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "PSU Bank", "groww": "state-bank-of-india"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom", "groww": "bharti-airtel"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors", "sector": "Auto", "groww": "tata-motors"},
    {"symbol": "ITC", "name": "ITC Ltd", "sector": "FMCG", "groww": "itc"},
    {"symbol": "LT", "name": "Larsen & Toubro", "sector": "Capital Goods", "groww": "larsen-and-toubro"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Banking", "groww": "kotak-mahindra-bank"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "sector": "NBFC", "groww": "bajaj-finance"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises", "sector": "Metals / Mining", "groww": "adani-enterprises"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharma", "sector": "Pharma", "groww": "sun-pharmaceutical-industries"},
    {"symbol": "ZOMATO", "name": "Zomato Ltd", "sector": "Consumer Internet", "groww": "zomato"},
    {"symbol": "TATASTEEL", "name": "Tata Steel", "sector": "Metals", "groww": "tata-steel"},
]

MIN_INTRADAY_RISK_PCT = 0.007   # 0.7% minimum move required to overcome STT & fees
SWING_PROFIT_TARGET_PCT = 0.08  # 8% target for delivery
