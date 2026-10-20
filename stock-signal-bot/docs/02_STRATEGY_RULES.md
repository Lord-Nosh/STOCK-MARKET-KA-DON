# Strategy Rules & Formulas

## 1. Intraday Long (BUY)
- **Timeframe**: 5-Minute Candles (Closed).
- **Confluence Checks**:
  1. `Close > VWAP`
  2. `9-EMA > 21-EMA`
  3. `55 <= RSI(14) <= 68`
  4. Positive buyer volume delta.
- **Risk & Target Formula**:
  - `Risk = max(Close * 0.007, 1.5 * ATR)`
  - `Stop Loss = Close - Risk`
  - `Target 1 = Close + (1.5 * Risk)` (Book 50%)
  - `Target 2 = Close + (2.5 * Risk)` (Trail remainder via 9-EMA)

## 2. Intraday Short (SELL)
- **Timeframe**: 5-Minute Candles (Closed).
- **Confluence Checks**:
  1. `Close < VWAP`
  2. `9-EMA < 21-EMA`
  3. `32 <= RSI(14) <= 45`
  4. Negative seller breakdown volume.
- **Risk & Target Formula**:
  - `Risk = max(Close * 0.007, 1.5 * ATR)`
  - `Stop Loss = Close + Risk`
  - `Target 1 = Close - (1.5 * Risk)`
  - `Target 2 = Close - (2.5 * Risk)`

## 3. Delivery / Swing (CNC)
- **Timeframe**: Daily Candles.
- **Rules**: `Close > 20-EMA > 50-EMA` + `RSI(14) > 50`.
- **Target**: `+8%` to `+15%` swing.
- **Stop Loss**: 3% below 50-Day EMA.
