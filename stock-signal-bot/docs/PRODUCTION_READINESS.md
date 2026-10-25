# Production-readiness status

**Status: research-only; not approved for live-money trading.**

This fork adds baseline safety guardrails, but it is not a substitute for validating the application in a real deployment. The online market-data implementation still calls the public Yahoo Finance chart endpoint. That endpoint is not a broker-authoritative real-time feed and must not be described as verified live NSE data.

## Changes in this hardening branch

- Restricts CORS to configured origins rather than allowing every origin.
- Protects operational backup and feed-health endpoints with `X-API-Key`; these endpoints fail closed when `SMKD_ADMIN_API_KEY` is not configured.
- Rejects non-finite/non-positive prices and invalid capital inputs in risk calculation.
- Returns zero shares instead of forcing a minimum one-share position when that position would exceed the calculated risk budget.
- Makes candidate signals wait when the risk sizing filter rejects the trade.
- Validates OHLCV as complete rows so filtered arrays and timestamps cannot become misaligned.
- Marks current public-feed observations as unverified/research-only and blocks execution-eligible BUY/SELL signals from that source.
- Fixes stale-feed provenance metadata so the serialized stale flag/reason reflects the freshness calculation.
- Removes tracked runtime SQLite/backup artifacts and ignores new ones.
- Adds regression tests and a backend test workflow.

## Required before paper trading

1. Integrate a licensed broker/exchange market-data provider with documented timestamps, instrument identifiers, session semantics, rate limits, reconnect handling, and terms permitting the intended use.
2. Wire that provider into the actual market-data path. The collector abstraction alone is not a provider integration.
3. Test provider failover, missing bars, stale data, exchange halts, clock skew, market holidays, and partial responses.
4. Implement a paper-trading ledger with order lifecycle events, realistic fees, spread, slippage, partial fills, rejection handling, and an auditable signal/strategy version.
5. Backtest multiple years and market regimes with survivorship and look-ahead controls; independently review the results.
6. Add deployment-specific authentication for user APIs, TLS, secret management, rate limits, logs/metrics/alerts, remote backups, and restore drills.
7. Run the automated test suite and review every failing test before deployment.

## Environment

Copy `.env.example` to `.env` locally. Generate a long random `SMKD_ADMIN_API_KEY` and configure the frontend origin(s) in `SMKD_CORS_ORIGINS`. Do not commit credentials.

Run the backend tests from `stock-signal-bot/backend`:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s app/tests -p "test_*.py" -v
```

The CI workflow runs this test command on pushes and pull requests. A passing test suite does not establish profitability, data-feed accuracy, regulatory compliance, or live-trading readiness.

## Signal semantics

A confluence score is a heuristic score, not a calibrated probability that a trade will win. Estimated transaction costs are assumptions until they are reconciled with the selected broker, instrument, exchange segment, and order type. Stop-loss orders do not guarantee the intended exit price through gaps or illiquid markets.

Do not add broker order-placement credentials or enable automatic live execution until the above gates have been independently verified.
