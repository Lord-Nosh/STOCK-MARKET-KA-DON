# Indian Short-Term Stock Signal & Opportunity Bot

Real-time Indian Stock Market (NSE) Signal Engine focused on **Intraday (Groww MIS)** and **Delivery (Groww CNC)** trading, powered by Python analysis backend and the high-performance **Zuari Framework (`@zuari/signals` + `@zuari/dom`)** front-end.

---

## 🚀 Architecture Overview

1. **Analysis Backend (`/backend/main.py`)**:
   - **Data Source**: Live Indian Market OHLCV data directly mapped for NSE (`.NS` tickers like `RELIANCE`, `TCS`, `HDFCBANK`, `INFY`, `TATAMOTORS`, etc.).
   - **Intraday Strategy (5-min intervals)**:
     - Volume-Weighted Average Price (**VWAP**) crossover detection.
     - Dual Exponential Moving Average (**9-EMA vs 21-EMA**) momentum slope.
     - Relative Strength Index (**14-period RSI**) overbought/oversold boundaries.
     - Automated Risk-Reward Level Calculations: Exact **Entry, Target 1, Target 2, and Stop Loss**.
   - **Delivery Strategy (Daily / Multi-Week Swing)**:
     - 20-Day and 50-Day moving average trends (**Golden Crossover**).
     - Trend confirmation and accumulation zones.
   - **Live News & Reasoning**:
     - Live Google News RSS feed aggregation for each Indian ticker.
     - Real-time sentiment tagging (Bullish, Bearish, Neutral) to identify news catalysts affecting stock pricing.
   - **Direct Groww App Integration**:
     - Direct deep links to open stock execution cards on Groww (`https://groww.in/stocks/...`).

2. **Ultra-Fast Frontend (`/fast-framework/packages/stock-bot-ui`)**:
   - Built on your **Zuari Framework** (`@zuari/signals`, `@zuari/dom`).
   - Zero Virtual-DOM overhead, sub-millisecond DOM part updates.
   - Separate dedicated tabs for:
     - ⚡ **Intraday Opportunities (Groww MIS)**
     - 📦 **Delivery / Positional (Groww CNC)**
     - 📰 **News Catalysts & Price Impact**

---

## 🛠️ How to Run

### Step 1: Start the Backend (FastAPI)
```powershell
cd backend
python -m uvicorn main:app --reload --port 8000
```
API docs will be available at `http://127.0.0.1:8000/docs`.

### Step 2: Start the Zuari Frontend (Vite)
In a separate terminal:
```powershell
cd fast-framework/packages/stock-bot-ui
pnpm run dev
```
Open your browser at `http://localhost:5173`.
