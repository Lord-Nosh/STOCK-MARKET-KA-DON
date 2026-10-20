# System Architecture & Directory Map

```
mm/
├── fast-framework/packages/stock-bot-ui/  # Zuari Zero-VDOM Reactive Web App
│   ├── src/
│   │   ├── types/index.ts                 # Clean TypeScript models
│   │   ├── state/store.ts                 # Zuari fine-grained signals & actions
│   │   ├── components/
│   │   │   ├── Header.ts                  # Market clock, session status, branding
│   │   │   ├── TabNavigation.ts           # Intraday / Delivery / News tabs
│   │   │   ├── Toolbar.ts                 # Search, live scan trigger
│   │   │   ├── IntradayCard.ts            # 5m MIS momentum, VWAP, levels, reasons
│   │   │   ├── DeliveryCard.ts            # CNC swing levels, EMAs, accumulation
│   │   │   └── NewsCard.ts                # Real-time sentiment, headlines
│   │   └── main.ts                        # Application bootstrap (< 40 lines)
│
├── stock-signal-bot/
│   ├── docs/                              # Lean, precise documentation
│   │   ├── 01_MARKET_TIMINGS.md           # IST intraday phases & trap avoidance
│   │   ├── 02_STRATEGY_RULES.md           # VWAP, EMA, RSI, ATR exact calculations
│   │   ├── 03_SCAM_PROTECTION.md          # 55-65% reality, repainting, fees & taxes
│   │   └── 04_API_SPECIFICATION.md        # Endpoints, schema, Groww link specs
│   └── backend/app/
│       ├── core/config.py                 # Universe (Nifty 100), timing bounds
│       ├── indicators/
│       │   ├── technicals.py              # Pure math: RSI, EMA, VWAP, ATR
│       │   └── calculations.py            # SL, Target 1, Target 2 risk calculator
│       ├── market/
│       │   ├── fetcher.py                 # NSE live tick & candle retrieval
│       │   └── sessions.py                # IST phase evaluator (trap vs prime)
│       ├── strategies/
│       │   ├── intraday.py                # 5m MIS high-momentum strategy
│       │   └── delivery.py                # Daily CNC swing trend strategy
│       ├── news/
│       │   └── sentiment.py               # RSS fetcher + headline NLP sentiment
│       ├── api/
│       │   └── routes.py                  # Lean FastAPI routers
│       └── main.py                        # Server entrypoint (< 30 lines)
```
