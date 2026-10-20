# API Specification

## Endpoints

### 1. `GET /api/session`
Returns current IST market status and active trading permission.
```json
{
  "phase": "PRIME_MOMENTUM_1",
  "can_trade_intraday": true,
  "ist_time": "10:30:15"
}
```

### 2. `GET /api/scan?filter_type=all`
Scans universe and returns ranked opportunities.
- Query params: `filter_type` (`all`, `intraday_buy`, `intraday_sell`, `delivery_buy`)

### 3. `GET /api/stock/{symbol}`
Detailed breakdown with technical indicators, levels, reasons, and news.

## Groww URL Scheme
```
https://groww.in/stocks/{company-slug}
```
Directly launches stock chart & order placement modal on Groww.
