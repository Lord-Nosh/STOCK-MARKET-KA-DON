import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict

BULLISH_KEYWORDS = ["surge", "jump", "profit", "gain", "high", "buy", "target", "soar", "deal", "growth", "record", "rally", "order", "expansion", "beat"]
BEARISH_KEYWORDS = ["drop", "fall", "loss", "plunge", "slump", "down", "probe", "cut", "sell", "penalty", "weak", "decline", "fine", "fraud", "miss"]

def fetch_ticker_news(symbol: str, company_name: str) -> List[Dict[str, str]]:
    """Aggregates and tags news catalysts for Indian equities"""
    query = urllib.parse.quote(f"{company_name} share NSE India")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    news_items = []
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            root = ET.fromstring(resp.read().decode('utf-8', errors='ignore'))
            for item in root.findall(".//item")[:4]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pubDate = item.find("pubDate").text if item.find("pubDate") is not None else ""

                lower = title.lower()
                b_cnt = sum(1 for w in BULLISH_KEYWORDS if w in lower)
                br_cnt = sum(1 for w in BEARISH_KEYWORDS if w in lower)

                sentiment = "BULLISH" if b_cnt > br_cnt else ("BEARISH" if br_cnt > b_cnt else "NEUTRAL")
                news_items.append({"title": title, "link": link, "published": pubDate, "sentiment": sentiment})
    except Exception as e:
        print(f"[NewsSentiment] Error for {symbol}: {e}")
    return news_items
