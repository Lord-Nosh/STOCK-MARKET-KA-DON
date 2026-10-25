# Architecture Overview

## Frontend
- **Package**: `fast-framework/packages/stock-bot-ui`
- **Build tool**: Vite (scripts `dev`, `build`, `preview`).
- **Chart library**: Lightweight Charts v5 (currently listed as a dependency).
- **Entry point**: `src/main.ts` creates the UI root and loads components.
- **Key components**:
  - `src/components/LiveCandleChart.ts` – renders interactive candlestick + volume.
  - `src/departments/StockDetailWorkspace.ts` – orchestrates market‑data display.
  - `src/state/store.ts` – holds reactive state (`stocks`, `selectedSymbol`, `signal_decision`).

## Backend
- **Package**: `stock-signal-bot/backend`
- **Framework**: FastAPI (entry `app/main.py`).
- **API**: `/api/scan` returns `UnifiedStockData` which includes `market_data.candles_5m` and `candles_daily` as parallel arrays.
- **Data contracts**: Defined in `src/types/index.ts` for UI; backend serialises matching JSON.

## Data Flow
1. Backend provides JSON with OHLC arrays (seconds timestamps).
2. Frontend fetches via `fetchScanData()` in `src/state/api.ts` and stores in `UnifiedStockData`.
3. `LiveCandleChart` consumes a normalized array of `MarketCandle` objects (UTC ms timestamps) for rendering.

## Module Responsibilities (per SMKD policy)
- **Provider adapters** – fetch and map raw market data → `MarketCandle`.
- **Indicator engine** – pure calculations (EMA, VWAP) – not yet implemented.
- **Chart layer** – visualises candles, volume, and price lines.
- **Risk engine** – validates entry/stop‑loss/target values.

The architecture respects the SMKD rule of a **single authoritative implementation** per business rule and keeps UI code independent of provider specifics.
