# QuantForge

Backtest a chronological price series against bounded long/short exposure signals, including turnover costs.

**Version0.2.0: local CPU research workbench.** Import a CSV, map the relevant columns, run the real calculation and inspect plots, tables and method assumptions. Export a JSON result report or exact replayable input. No API key, GPU, paid service or external model call is required.

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

Require positive prices and equally long signal/price arrays with at least four values. Exposure signals must lie between−1 and1. Source rows must already be ordered chronologically. There is no timestamp alignment, automatic strategy discovery, benchmark construction or execution engine.

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

Node is needed only for frontend development checks. Fresh rebuild evidence is in `evidence/rebuild/`. No Docker runtime, remote CI, publication or human review is implied merely by creating files. Required CI must pass before merging. Containers bind localhost and run nonroot; add authentication, HTTPS and deployment resource limits before external access. MIT license.
