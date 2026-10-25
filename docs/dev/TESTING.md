# Testing Guide

## Prerequisites
- Node 20+ (for `pnpm`).
- Python 3.11+ (for backend tests).
- All workspace dependencies already installed (`pnpm install` run at repo root).

## Frontend
```bash
# Run unit / UI tests (Vitest)
pnpm -C fast-framework/packages/stock-bot-ui test

# Run the Vite dev server (watch mode)
pnpm -C fast-framework/packages/stock-bot-ui dev
```
- Expected outcome: test runner exits with `0` and prints `PASS` for each suite. The dev server should start without JSON parse errors.

## Backend
```bash
# Run all FastAPI tests (pytest)
pytest stock-signal-bot/backend/tests
```
- Expected outcome: `0` failures, all HTTP‑200 responses for the scan endpoint.

## Build
```bash
# Frontend production build
pnpm -C fast-framework/packages/stock-bot-ui build
```
- Expected outcome: `vite build` finishes with exit code `0` and creates the `dist/` folder.

## Known Limitations
- The chart integration tests are not present yet; they will be added after the data‑adapter is implemented.
- Backend tests assume the mock market‑data provider is reachable; if the external API is down, tests will be skipped.

## Recording Results
Whenever a command is run, capture the full stdout/stderr and paste it into the next status checkpoint (see `STATUS.md`). Do **not** claim success without the actual command output.
