---
name: smkd-api-contract
description: Use when modifying backend FastAPI endpoints, Pydantic schemas, or frontend API clients. Enforces synchronized types and contract consistency.
---

# SMKD API Contract & Schema Sync Procedure

Use this procedure when an API route, query parameter, or response model is added or modified.

## Scope
- Backend route: `stock-signal-bot/backend/app/api/`
- Frontend API client & types: `fast-framework/packages/stock-bot-ui/src/state/`
- Documentation & contract specs: `docs/contracts/`

## Procedure
1. **Define Schema**:
   - Establish Pydantic model in FastAPI backend.
   - Run verification test or check endpoint response contract.
2. **Sync Frontend Client**:
   - Update TypeScript interfaces and client functions in `stock-bot-ui`.
   - Ensure null-safety and default value handling.
3. **Verify Compatibility**:
   - Run type checks / build across both backend and frontend.
4. **Document**:
   - Update contract reference in `docs/contracts/` if public API is changed.
