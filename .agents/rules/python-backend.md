---
description: Conditional rules for modifying Python backend services, FastAPI endpoints, indicators, and sqlite data.
globs: stock-signal-bot/backend/**/*.py
---

# Python Backend & Signal Bot Rules

- Maintain compatibility with FastAPI and Pydantic models.
- Never write ad-hoc SQL that modifies production tables or deletes sqlite databases (`signals_tree.db`).
- Validate incoming market data candles for null/NaN values before feeding them into indicator calculations.
- Keep indicator calculations purely deterministic; avoid mutating global state across requests.
- When an API endpoint response format changes, simultaneously update the corresponding TypeScript API client in `packages/stock-bot-ui`.
