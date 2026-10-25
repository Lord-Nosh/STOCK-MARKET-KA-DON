# SMKD — Codebase Map & Module Directory

This document defines module boundaries, ownership, dependencies, and safe-change procedures for SMKD.

---

## 1. Backend Architecture (`stock-signal-bot/backend/`)

### Module: `scanner-api`
- **Path**: [`stock-signal-bot/backend/app/api/routes.py`](file:///c:/Users/disha/Documents/CODES/money/mm/stock-signal-bot/backend/app/api/routes.py)
- **Responsibility**: HTTP routes (`/scan`, `/stock/{symbol}`, `/overview`), query validation, partial-scan fault tolerance, and 503 handling when feeds are unavailable.
- **Inputs**: Universe configurations, market intelligence, market data feed streams.
- **Outputs**: JSON payloads (`results`, `count`, `failed_symbols`, `is_partial`).
- **Consumers**: Frontend API client (`stock-bot-ui/src/state/api.ts`), test suites.
- **Safe Change Procedure**:
  1. Inspect response model fields.
  2. If altering output shapes, update TypeScript types in `stock-bot-ui/src/state/api.ts` and `store.ts`.
  3. Run `python -m unittest stock-signal-bot/backend/app/tests/test_trading_correctness.py`.

### Module: `market-data-service`
- **Path**: [`stock-signal-bot/backend/app/departments/market_data/service.py`](file:///c:/Users/disha/Documents/CODES/money/mm/stock-signal-bot/backend/app/departments/market_data/service.py)
- **Responsibility**: Fetching 5m & daily candles, Yahoo Finance API parsing, in-memory 10s caching, offline replay hook (`ReplayMarketDataProvider`).
- **Inputs**: Symbols, tickers (`RELIANCE.NS`), environment mode (`SMKD_DATA_MODE`).
- **Outputs**: Normalized candle dictionaries with timestamps, opens, highs, lows, closes, volumes.
- **Consumers**: `routes.py`, technical indicator department, intraday strategy.
- **Verification**: `python -m unittest stock-signal-bot/backend/app/tests/test_provider_replay.py`.

### Module: `technical-indicators`
- **Path**: [`stock-signal-bot/backend/app/indicators/technicals.py`](file:///c:/Users/disha/Documents/CODES/money/mm/stock-signal-bot/backend/app/indicators/technicals.py)
- **Responsibility**: Pure numeric indicator calculations (RSI, EMA 9/21, ATR 14, VWAP). Returns `None` when candles are insufficient.
- **Verification**: `python -m unittest stock-signal-bot/backend/app/tests/test_calculations_edge_cases.py`.

### Module: `intraday-strategy`
- **Path**: [`stock-signal-bot/backend/app/strategies/intraday.py`](file:///c:/Users/disha/Documents/CODES/money/mm/stock-signal-bot/backend/app/strategies/intraday.py)
- **Responsibility**: Confluence evaluation, decision logic (`BUY`, `SELL`, `WAIT`), dynamic stop-loss, targets.

---

## 2. Frontend Workspace Architecture (`fast-framework/packages/stock-bot-ui/`)

### Module: `stock-detail-workspace`
- **Path**: [`fast-framework/packages/stock-bot-ui/src/departments/StockDetailWorkspace.ts`](file:///c:/Users/disha/Documents/CODES/money/mm/fast-framework/packages/stock-bot-ui/src/departments/StockDetailWorkspace.ts)
- **Responsibility**: Stock detail stage, rendering active market data, subtabs (`chart`, `indicators`, `orderbook`), and error states.
- **Consumers**: `main.ts`, user click interactions.
- **Verification**: `pnpm -C fast-framework exec vitest run src/tests/ui_quality_pass.test.ts`.

### Module: `candle-chart-renderer`
- **Path**: [`fast-framework/packages/stock-bot-ui/src/components/CandleChart.ts`](file:///c:/Users/disha/Documents/CODES/money/mm/fast-framework/packages/stock-bot-ui/src/components/CandleChart.ts)
- **Responsibility**: SVG candlestick chart renderer with volume bars, VWAP/EMA overlays, and supply/demand zones.
- **Verification**: Monorepo vitest suite and `pnpm -C fast-framework/packages/stock-bot-ui build`.

### Module: `state-store`
- **Path**: [`fast-framework/packages/stock-bot-ui/src/state/store.ts`](file:///c:/Users/disha/Documents/CODES/money/mm/fast-framework/packages/stock-bot-ui/src/state/store.ts)
- **Responsibility**: Central reactive signals store (`currentStock`, `stocks`, `feedHealth`, `scanError`), polling loops, 503 error handling.
