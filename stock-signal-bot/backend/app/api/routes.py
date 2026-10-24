from fastapi import APIRouter, Query
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from app.core.config import TRACKED_UNIVERSE, ACCOUNT_CAPITAL
from app.departments.market_data.service import market_data_dep
from app.departments.technical_analysis.service import technical_dep
from app.departments.fundamental_analysis.service import fundamental_dep
from app.departments.market_intelligence.service import market_intelligence_dep
from app.departments.signal_risk.service import signal_risk_dep

from app.backtesting.backtest_engine import run_historical_backtest
from app.db.database import record_analysis_tree, get_tree_history
from app.db.backup import backup_service
from app.departments.market_data.collector import collector_service

router = APIRouter()

def process_unified_stock(stock: Dict[str, str], intelligence: Dict[str, Any], capital: float = ACCOUNT_CAPITAL) -> Dict[str, Any]:
    symbol = stock["symbol"]
    ticker = stock.get("ticker", f"{symbol}.NS")
    name = stock["name"]
    sector = stock["sector"]
    groww_slug = stock["groww"]

    # 1. Market Data Department (Shared Data Layer)
    m_data = market_data_dep.get_stock_data(symbol, ticker)
    if not m_data:
        m_data = {
            "symbol": symbol, "ticker": ticker, "current_price": 1000.0, "change_pct": 0.0,
            "day_high": 1010.0, "day_low": 990.0, "volume_today": 100000,
            "candles_5m": {"opens": [], "highs": [], "lows": [], "closes": [], "volumes": []},
            "candles_daily": {"closes": []}
        }

    # 2. Technical Analysis Department
    technicals = technical_dep.analyze(m_data)

    # 3. Fundamental Analysis Department
    fundamentals = fundamental_dep.analyze(symbol, name)

    # 4. Signal & Risk Engine Department (Final Decision Synthesis)
    decision = signal_risk_dep.synthesize_decision(
        market_data=m_data,
        technicals=technicals,
        fundamentals=fundamentals,
        intelligence=intelligence,
        capital=capital
    )

    return {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "current_price": m_data["current_price"],
        "change_pct": m_data["change_pct"],
        "day_high": m_data["day_high"],
        "day_low": m_data["day_low"],
        "groww_url": f"https://groww.in/stocks/{groww_slug}",
        # Department outputs clearly separated
        "market_data": {
            "volume_today": m_data["volume_today"],
            "timestamp": m_data.get("timestamp", 0)
        },
        "technicals": technicals,
        "fundamentals": fundamentals,
        "signal_decision": decision,
        # Backward-compatible intraday accessor
        "intraday": {
            "signal": decision["signal"],
            "confluence_score": decision["confluence_score"],
            "confidence": decision["confidence"],
            "entry": decision["entry"],
            "target_1": decision["target_1"],
            "target_2": decision["target_2"],
            "stop_loss": decision["stop_loss"],
            "vwap": technicals["vwap"],
            "rsi": technicals["rsi"],
            "ema_9": technicals["ema_9"],
            "ema_21": technicals["ema_21"],
            "atr": technicals["atr"],
            "adx": technicals["adx"],
            "rvol": technicals["rvol"],
            "sparkline": technicals["sparkline"],
            "market_structure": technicals["market_structure"],
            "supply_demand": technicals["supply_demand"],
            "key_candle": technicals["key_candle"],
            "risk_sizing": decision["risk_sizing"],
            "reasons": decision["reasons"]
        },
        "news": fundamentals["news"]
    }

@router.get("/overview")
def get_overview():
    """Returns top-level market overview and intelligence"""
    intelligence = market_intelligence_dep.get_intelligence()
    return intelligence

@router.get("/scan")
def scan_all(capital: float = Query(ACCOUNT_CAPITAL)):
    """Runs parallel scan through all 6 departments"""
    intelligence = market_intelligence_dep.get_intelligence()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda s: process_unified_stock(s, intelligence, capital=capital), TRACKED_UNIVERSE))

    # Snapshot to database tree
    try:
        record_analysis_tree(
            market_phase=intelligence["session"]["phase"],
            ist_time=intelligence["session"]["ist_time"],
            stocks_data=results
        )
    except Exception as e:
        print(f"[DB Warning]: {e}")

    # Default sort by confluence score
    results.sort(key=lambda x: (x.get("signal_decision", {}).get("confluence_score", 0)), reverse=True)

    return {
        "intelligence": intelligence,
        "count": len(results),
        "results": results
    }

@router.get("/stock/{symbol}")
def get_single_stock(symbol: str, capital: float = Query(ACCOUNT_CAPITAL)):
    sym = symbol.upper()
    stock = next((s for s in TRACKED_UNIVERSE if s["symbol"] == sym), {"symbol": sym, "name": sym, "sector": "NSE", "groww": sym.lower()})
    intelligence = market_intelligence_dep.get_intelligence()
    return process_unified_stock(stock, intelligence, capital=capital)

@router.get("/backtest/{symbol}")
def backtest(symbol: str, days: int = Query(5, ge=1, le=30)):
    return run_historical_backtest(symbol.upper(), days)

@router.get("/tree-history")
def tree_history(limit: int = Query(10, ge=1, le=50)):
    return get_tree_history(limit)

@router.post("/system/backup")
def trigger_system_backup():
    """Trigger an atomic point-in-time snapshot backup of the database."""
    return backup_service.create_snapshot_backup()

@router.get("/system/backups")
def list_system_backups():
    """List available database backups and point-in-time recovery archives."""
    return {"backups": backup_service.list_backups()}

@router.get("/system/feed-health/{symbol}")
def check_feed_health(symbol: str):
    """Check health and freshness of the market feed for a given symbol."""
    is_healthy, status = collector_service.check_feed_health(symbol.upper())
    return {
        "symbol": symbol.upper(),
        "is_healthy": is_healthy,
        "status": status,
        "active_provider": collector_service.active_provider
    }
