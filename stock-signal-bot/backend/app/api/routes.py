import os
import secrets
from fastapi import APIRouter, Header, Query, HTTPException, status
from typing import Dict, Any, List, Optional
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


def _require_admin_key(provided_key: Optional[str]) -> None:
    """Fail closed for operational endpoints unless an admin key is configured."""
    expected_key = os.getenv("SMKD_ADMIN_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrative endpoints are disabled until SMKD_ADMIN_API_KEY is configured",
        )
    if not provided_key or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid X-API-Key header required",
        )


def process_unified_stock(
    stock: Dict[str, str],
    intelligence: Dict[str, Any],
    capital: float = ACCOUNT_CAPITAL,
) -> Optional[Dict[str, Any]]:
    symbol = stock["symbol"]
    ticker = stock.get("ticker", f"{symbol}.NS")
    name = stock["name"]
    sector = stock["sector"]
    groww_slug = stock["groww"]

    # 1. Market Data Department (Shared Data Layer)
    m_data = market_data_dep.get_stock_data(symbol, ticker)
    if not m_data:
        return None

    # 2. Technical Analysis Department
    technicals = technical_dep.analyze(m_data)

    # 3. Fundamental Analysis Department
    fundamentals = fundamental_dep.analyze(symbol, name)

    # 4. Signal & Risk Engine
    decision = signal_risk_dep.synthesize_decision(
        market_data=m_data,
        technicals=technicals,
        fundamentals=fundamentals,
        intelligence=intelligence,
        capital=capital,
    )

    # Yahoo's public chart endpoint is not a broker-authoritative feed. Keep its
    # analysis visible for research, but do not expose an actionable BUY/SELL.
    # A verified broker/exchange feed adapter must explicitly set signal_eligible.
    feed_signal_eligible = m_data.get("signal_eligible") is True
    if not feed_signal_eligible and decision.get("signal") in {"BUY CANDIDATE", "SELL CANDIDATE"}:
        decision["research_signal"] = decision["signal"]
        decision["signal"] = "WAIT"
        decision["execution_eligible"] = False
        decision["reasons"] = list(decision.get("reasons", [])) + [
            "Execution blocked: market-data provider is not verified as broker/exchange-authoritative. "
            "Treat this setup as research-only."
        ]
    else:
        decision["execution_eligible"] = bool(feed_signal_eligible and decision.get("risk_sizing", {}).get("trade_allowed"))

    return {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "current_price": m_data["current_price"],
        "change_pct": m_data["change_pct"],
        "day_high": m_data["day_high"],
        "day_low": m_data["day_low"],
        "groww_url": f"https://groww.in/stocks/{groww_slug}",
        "market_data": {
            "volume_today": m_data["volume_today"],
            "timestamp": m_data.get("timestamp", 0),
            "provider_timestamp": m_data.get("provider_timestamp"),
            "received_at": m_data.get("received_at", m_data.get("timestamp", 0)),
            "data_source": m_data.get("data_source", "UNKNOWN"),
            "data_mode": m_data.get("data_mode", "UNKNOWN"),
            "signal_eligible": feed_signal_eligible,
            "data_quality": m_data.get("data_quality", {}),
            "candles_5m": m_data.get("candles_5m", {}),
            "candles_daily": m_data.get("candles_daily", {}),
        },
        "technicals": technicals,
        "fundamentals": fundamentals,
        "signal_decision": decision,
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
            "reasons": decision["reasons"],
        },
        "news": fundamentals["news"],
    }


@router.get("/overview")
def get_overview():
    """Returns top-level market overview and intelligence."""
    return market_intelligence_dep.get_intelligence()


@router.get("/scan")
def scan_all(capital: float = Query(ACCOUNT_CAPITAL, gt=0, le=1_000_000_000_000)):
    """Runs a parallel scan with partial-failure resilience."""
    intelligence = market_intelligence_dep.get_intelligence()
    failed_symbols: List[str] = []

    def _safe_process(stock: Dict[str, str]) -> Optional[Dict[str, Any]]:
        try:
            result = process_unified_stock(stock, intelligence, capital=capital)
            if result is None:
                failed_symbols.append(stock["symbol"])
            return result
        except Exception:
            failed_symbols.append(stock["symbol"])
            return None

    with ThreadPoolExecutor(max_workers=min(10, max(1, len(TRACKED_UNIVERSE)))) as executor:
        raw_results = list(executor.map(_safe_process, TRACKED_UNIVERSE))

    results = [result for result in raw_results if result is not None]
    if not results and TRACKED_UNIVERSE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Market data unavailable for all {len(TRACKED_UNIVERSE)} tracked symbols",
        )

    try:
        record_analysis_tree(
            market_phase=intelligence["session"]["phase"],
            ist_time=intelligence["session"]["ist_time"],
            stocks_data=results,
        )
    except Exception:
        # The scan remains usable if history persistence is temporarily unavailable.
        pass

    results.sort(
        key=lambda result: result.get("signal_decision", {}).get("confluence_score", 0),
        reverse=True,
    )
    return {
        "intelligence": intelligence,
        "count": len(results),
        "results": results,
        "failed_symbols": sorted(set(failed_symbols)),
        "is_partial": bool(failed_symbols),
    }


@router.get("/stock/{symbol}")
def get_single_stock(
    symbol: str,
    capital: float = Query(ACCOUNT_CAPITAL, gt=0, le=1_000_000_000_000),
):
    sym = symbol.upper()
    stock = next(
        (item for item in TRACKED_UNIVERSE if item["symbol"] == sym),
        {"symbol": sym, "ticker": f"{sym}.NS", "name": sym, "sector": "NSE", "groww": sym.lower()},
    )
    intelligence = market_intelligence_dep.get_intelligence()
    result = process_unified_stock(stock, intelligence, capital=capital)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Market data unavailable for symbol {sym}",
        )
    return result


@router.get("/backtest/{symbol}")
def backtest(symbol: str, days: int = Query(5, ge=1, le=30)):
    return run_historical_backtest(symbol.upper(), days)


@router.get("/tree-history")
def tree_history(limit: int = Query(10, ge=1, le=50)):
    return get_tree_history(limit)


@router.post("/system/backup")
def trigger_system_backup(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """Trigger a database backup; disabled until an admin API key is configured."""
    _require_admin_key(x_api_key)
    return backup_service.create_snapshot_backup()


@router.get("/system/backups")
def list_system_backups(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """List backups; disabled until an admin API key is configured."""
    _require_admin_key(x_api_key)
    return {"backups": backup_service.list_backups()}


@router.get("/system/feed-health/{symbol}")
def check_feed_health(
    symbol: str,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """Expose operational feed health only to an authenticated administrator."""
    _require_admin_key(x_api_key)
    is_healthy, feed_status = collector_service.check_feed_health(symbol.upper())
    return {
        "symbol": symbol.upper(),
        "is_healthy": is_healthy,
        "status": feed_status,
        "active_provider": collector_service.active_provider,
    }
