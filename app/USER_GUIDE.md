# QuantForge user guide — v0.3.0

## What this tool does

Backtest a chronological price series against bounded long/short exposure signals, including turnover costs.

Use case: A researcher has an exposure rule computed from previously available information and wants to see its historical net equity, drawdowns and cost sensitivity.

## Quickstart

Requires Docker Compose, or Python3.12+ for the installed pinned NumPy dependency. No API key, remote model, GPU or paid service is used.

```sh
docker compose up --build
```

Open http://127.0.0.1:8000. The interactive workbench loads a clearly labeled synthetic example. API docs: http://127.0.0.1:8000/docs. Change the host port in compose if running several tools together.

Without Docker:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Walkthrough

1. Load the synthetic 48-row example. Map `prices` and `signals`.
2. Keep costs at 5 basis points and annualization at 252 for daily observations. Choose a different periods-per-year value for other sampling intervals.
3. Run backtest. Inspect net equity, total net return, maximum drawdown and the period table.
4. Increase turnover costs and rerun; compare results by exporting both reports.
5. Export replayable input for an exact API reproduction.

## Import and mapping

Import UTF-8 CSV with unique, nonempty header names. A BOM, CRLF, quoted commas, doubled quote escapes and quoted multiline fields are supported. Every data row must contain the same number of fields. Blank physical lines are ignored; empty fields within rows are not silently removed. The preview displays the first eight rows, while analysis uses all imported rows. Use mapping controls to select numeric columns; extra columns can remain unused. Import provenance is displayed as unverified, and imported values render as text.

Files and API requests are bounded at2MiB. CSV permits up to100 columns and100,000 rows; selected numeric matrices permit at most50 columns. Numbers must be finite with magnitude at most1e100. Imported files are read locally by the browser; selected data are sent to the local FastAPI service. The service holds requests in memory and does not persist them. No external network request is required by the workbench.

CSV format illustration (this fragment may be below the minimum sample size):

```csv
prices,signals
100,0
110,1
121,1
121,0
```

Input requirements: Require positive prices and equally long signal/price arrays with at least four values. Exposure signals must lie between−1 and1. Source rows must already be ordered chronologically. A fixed cost-free buy-and-hold comparator is included. There is no timestamp alignment, automatic strategy discovery, custom benchmark construction or execution engine.

## Methods

The signal at index t multiplies price return from t to t+1. Position change from the previous period (initially cash) determines turnover. Costs = turnover × basis points / 10,000. Net returns compound from equity1. Maximum drawdown includes the initial equity peak; Sharpe uses sample volatility and a zero risk-free rate. The final signal has no next return and is intentionally unused.

## Read the output

Total return is compounded, while total_cost_fraction is the simple sum of per-period turnover deductions and should not be subtracted from total return again. Equity and net-return arrays expose the complete computation. A null Sharpe indicates negligible volatility.

The workbench provides metric cards, a plot, interpretation and exact result table. For long time sequences, the table shows the first300 rows; the API report includes the complete arrays. Charts summarize calculations, not additional fitted models. The expandable API response exposes exact values. Change any mapping or parameter to clear old results, then rerun; an in-flight result is discarded if settings changed.

## Export and replay

**Export result report (JSON)** downloads application/version, timestamp, provenance label, mapping/settings and computed result. **Export replayable input (JSON)** includes selected numeric data and is exactly the `/analyze` request format. Exports are local downloads; review them for sensitive data before sharing. There is no result CSV export and therefore no spreadsheet-formula export interpretation. Synthetic example CSV uses only fixed headers/numeric values.

```sh
curl --fail -H 'Content-Type: application/json' --data-binary @examples/synthetic.json http://127.0.0.1:8000/analyze
curl --fail -H 'Content-Type: application/json' --data-binary @downloaded-analysis-input.json http://127.0.0.1:8000/analyze
```

{"prices":[100,110,121,121],"signals":[0,1,1,0],"cost_bps":100,"periods_per_year":252}

## Assumptions and limits

No financing, short borrow cost, leverage/margin model, terminal liquidation fee, market impact or external transaction is modeled. A signal constructed using future information remains biased even though the engine applies it with a one-period lag. These are historical research calculations, not an investment recommendation.

These are bounded local research tools. Synthetic fixtures do not establish external scientific validity. No domain expert or human audit is claimed. For network exposure, configure authentication, HTTPS, rate limits and deployment concurrency/memory bounds. Defaults bind to localhost and containers run without root privileges.

## Troubleshooting

Nonpositive price: correct the source or remove invalid observations intentionally before import. Exposure outside bounds: normalize your desired fractional positions. Exhausted equity: reduce exposure/costs or use an appropriate margin-aware simulator. Zero-variance returns: expect undefined Sharpe.

CSV row/column error: fix the named row; do not convert a missing observation to zero automatically. HTTP422: inspect the specific schema/algorithm message and adjust mapping or input. HTTP413: reduce selected rows/columns below the2MiB request bound. File parse errors clear the usable dataset and results. For a browser error, inspect local service availability; restart only after reviewing the service log. If a download fails, check browser download permissions.

## Reproducibility and checks

```sh
pytest -q
node tools/test_ui.mjs
pip-audit --strict
bandit -r app -ll
```

Python tests exercise numerical results and actual HTTP endpoints. Node tests exercise CSV parsing, column mapping, numeric rejection and the synthetic analysis payload. Node22+ is used for development checks; it is not a runtime service dependency. Fresh v0.3.0 developer evidence is under `evidence/improvements-0.3/`; it records what was run and does not establish unexecuted Docker, GitHub CI or human validation. Configure required CI checks and never merge a failing release.

MIT license; see LICENSE.

## v0.3.0: benchmark and cost attribution

The workbench now plots three aligned equity series: net strategy, gross strategy and cost-free buy-and-hold. Buy-and-hold equity is exactly each observed price divided by the first price, over the same first/last observations as the strategy. It is a **cost-free comparator**: no initial entry, exit, financing or other cost. It deliberately does not apply strategy turnover costs. A net-minus-benchmark return difference is descriptive, not estimated alpha or a like-for-like transaction-cost-adjusted comparison.

The response adds `gross_equity`, `gross_total_return`, `period_turnover`, `period_cost_fractions`, `benchmark` (equity, returns, total return, drawdown, Sharpe and assumptions), `cost_impact_return_points` and `net_minus_benchmark_return_points`. Original fields remain. Cost impact is gross final equity minus net final equity, including compounding, and differs from the simple sum of period costs. API return-point fields are fractions: 0.011 means 1.1 percentage points (the UI labels `pp`). Period costs still use the original additive return convention.

Example: prices100→110→121→121, exposure1 throughout, cost100 basis points on initial turnover1 gives gross return21%, net19.9%, compounded impact1.1 percentage points and summed period cost1%. Without costs, full exposure matches the benchmark. The performance table compares drawdowns and zero-risk-free Sharpe on identical periods. Exported reports include all new arrays and diagnostics. No execution or financial transactions occur.
