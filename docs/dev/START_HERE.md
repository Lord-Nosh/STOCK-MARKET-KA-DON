# SMKD — Developer Onboarding & Quick Start Guide

Welcome to the **SMKD (Money-Market)** repository. This document is the single entry point for all developers and AI coding agents.

---

## 1. Fast Overview & System Architecture

SMKD is an institutional stock-market signal scanner and trading intelligence platform consisting of:
- **Backend**: FastAPI Python engine located at `stock-signal-bot/backend/`. Handles multi-department market intelligence, technical indicators (RSI, EMA, ATR, VWAP), intraday strategies, and signal persistence in SQLite (`signals_tree.db`).
- **Frontend**: High-performance UI located at `fast-framework/packages/stock-bot-ui/` built on Vite, Zuari signals reactive architecture, and interactive candlestick charting.
- **Submodule (`fast-framework`)**: Monorepo hosting reactive UI primitives, presets, signals, and the `stock-bot-ui` app.

---

## 2. Quick Start & Prerequisites

Verify developer environment health before making any changes:

```powershell
# 1. Run environment health doctor
.\scripts\dev\devctl.ps1 doctor

# 2. Run backend test suite (Offline Replay Mode)
$env:PYTHONPATH="stock-signal-bot/backend"
python -m unittest discover -s stock-signal-bot/backend/app/tests

# 3. Run frontend test suite
pnpm -C fast-framework test

# 4. Build frontend workspace
pnpm -C fast-framework/packages/stock-bot-ui build
```

---

## 3. Developer Navigation Map

| Question | Documentation Link |
| :--- | :--- |
| **Where do I make a change?** | [docs/dev/CODEBASE_MAP.md](file:///c:/Users/disha/Documents/CODES/money/mm/docs/dev/CODEBASE_MAP.md) |
| **How should I change it safely?** | [docs/dev/CHANGE_GUIDE.md](file:///c:/Users/disha/Documents/CODES/money/mm/docs/dev/CHANGE_GUIDE.md) |
| **What rules map code to docs?** | [docs/dev/DOCS_MAP.yml](file:///c:/Users/disha/Documents/CODES/money/mm/docs/dev/DOCS_MAP.yml) |
| **What is currently broken / in-progress?** | [docs/dev/STATUS.md](file:///c:/Users/disha/Documents/CODES/money/mm/docs/dev/STATUS.md) |
| **What are our autonomy & safety rules?** | [AGENTS.md](file:///c:/Users/disha/Documents/CODES/money/mm/AGENTS.md) |
| **How do I manage task transactions?** | [scripts/dev/devctl.ps1](file:///c:/Users/disha/Documents/CODES/money/mm/scripts/dev/devctl.ps1) |

---

## 4. Standard 10-Step Development Workflow

1. Read this guide (`START_HERE.md`).
2. Run `.\scripts\dev\devctl.ps1 doctor` to verify baseline health.
3. Check `STATUS.md` for known blockers.
4. Locate the target module in `CODEBASE_MAP.md`.
5. Create a change-impact plan using the template in `CHANGE_GUIDE.md`.
6. Initialize task tracking via `.\scripts\dev\devctl.ps1 create -TaskId <ID> -Title <Title>`.
7. Implement the smallest correct patch following local conventions.
8. Execute focused tests and regression test suites.
9. Run `.\scripts\dev\update-docs.ps1 --dry-run` to see affected documentation.
10. Finalize verification via `.\scripts\dev\devctl.ps1 verify -TaskId <ID>`.
