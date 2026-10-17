# QuantForge

Backtest a chronological price series against bounded long/short exposure signals, including turnover costs.

**Version 0.3.0: local CPU research workbench.** Import a CSV, map the relevant columns, run the real calculation and inspect plots, tables and method assumptions. Export a JSON result report or exact replayable input. No API key, GPU, paid service or external model call is required.

## Why use it

A researcher has an exposure rule computed from previously available information and wants to see its historical net equity, drawdowns and cost sensitivity.

## Start

```sh
docker compose up --build
```

Open http://127.0.0.1:8000 and choose **Load synthetic example**. All bundled data are explicitly synthetic. Import your own UTF-8 CSV to use actual observations; their provenance remains unverified by the application.

Python3.12+ alternative:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API example:

```sh
curl --fail -H 'Content-Type: application/json' --data-binary @examples/synthetic.json http://127.0.0.1:8000/analyze
```

## Inputs, outputs and scientific scope

Require positive prices and equally long signal/price arrays with at least four values. Exposure signals must lie between−1 and1. Source rows must already be ordered chronologically. A fixed cost-free buy-and-hold comparator is included. There is no timestamp alignment, automatic strategy discovery, custom benchmark construction or execution engine.

Total return is compounded, while total_cost_fraction is the simple sum of per-period turnover deductions and should not be subtracted from total return again. Equity and net-return arrays expose the complete computation. A null Sharpe indicates negligible volatility.

No financing, short borrow cost, leverage/margin model, terminal liquidation fee, market impact or external transaction is modeled. A signal constructed using future information remains biased even though the engine applies it with a one-period lag. These are historical research calculations, not an investment recommendation.

Read the [complete user guide](docs/USER_GUIDE.md) for the walkthrough, methods, export/replay, data limits and troubleshooting. A CSV sample is in `examples/synthetic.csv`; the JSON example calls the same API.

## Validate

```sh
pip install '.[dev]'
pytest -q
node tools/test_ui.mjs
pip-audit --strict
bandit -r app -ll
```

Node is needed only for frontend development checks. Fresh v0.3.0 developer evidence is in `evidence/improvements-0.3/`; previous v0.2 records remain historical. No Docker runtime, remote CI, publication or human review is implied merely by creating files. Required CI must pass before merging. Containers bind localhost and run nonroot; add authentication, HTTPS and deployment resource limits before external access. MIT license.

## v0.3.0: benchmark and cost attribution

The workbench now plots three aligned equity series: net strategy, gross strategy and cost-free buy-and-hold. Buy-and-hold equity is exactly each observed price divided by the first price, over the same first/last observations as the strategy. It is a **cost-free comparator**: no initial entry, exit, financing or other cost. It deliberately does not apply strategy turnover costs. A net-minus-benchmark return difference is descriptive, not estimated alpha or a like-for-like transaction-cost-adjusted comparison.

The response adds `gross_equity`, `gross_total_return`, `period_turnover`, `period_cost_fractions`, `benchmark` (equity, returns, total return, drawdown, Sharpe and assumptions), `cost_impact_return_points` and `net_minus_benchmark_return_points`. Original fields remain. Cost impact is gross final equity minus net final equity, including compounding, and differs from the simple sum of period costs. API return-point fields are fractions: 0.011 means 1.1 percentage points (the UI labels `pp`). Period costs still use the original additive return convention.

Example: prices100→110→121→121, exposure1 throughout, cost100 basis points on initial turnover1 gives gross return21%, net19.9%, compounded impact1.1 percentage points and summed period cost1%. Without costs, full exposure matches the benchmark. The performance table compares drawdowns and zero-risk-free Sharpe on identical periods. Exported reports include all new arrays and diagnostics. No execution or financial transactions occur.
