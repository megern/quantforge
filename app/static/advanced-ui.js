"use strict";
function renderPortfolio(value) {
  const get = (id) => document.getElementById(id);
  table(
    get("portfolio-table"),
    ["Portfolio metric", "Value"],
    [
      ["Net return", percent(value.total_return)],
      ["Max drawdown", percent(value.max_drawdown)],
      ["Initial allocation fee", format(value.initial_allocation_cost)],
      [
        "Total fees (initial-capital units)",
        format(value.total_cost_in_initial_capital_units),
      ],
      ["L1 turnover", format(value.total_turnover)],
      ...value.asset_contributions.map((row) => [
        row.asset + " gain contribution",
        format(row.gain_in_initial_capital_units),
      ]),
    ],
  );
  const extra = element("div");
  table(
    extra,
    ["Return correlation", ...value.asset_names],
    value.correlation.map((row, i) => [
      value.asset_names[i],
      ...row.map((v) => format(v)),
    ]),
  );
  get("portfolio-table").append(extra);
  const audit = element("div");
  audit.append(
    element("h3", "Rebalance audit (first 100 periods; full data in report)"),
  );
  const auditTable = element("div");
  table(
    auditTable,
    [
      "End row (1-based)",
      "Rebalance",
      "Turnover",
      "Fee",
      "Starting weights",
      "Drift weights",
      "Net equity",
    ],
    value.periods
      .slice(0, 100)
      .map((row) => [
        row.end_row_index + 1,
        row.rebalance ? "Yes" : "No",
        format(row.turnover),
        format(row.cost_in_initial_capital_units),
        row.starting_weights
          .map((v, i) => value.asset_names[i] + ": " + percent(v))
          .join("; "),
        row.pre_rebalance_weights
          .map((v, i) => value.asset_names[i] + ": " + percent(v))
          .join("; "),
        format(row.net_equity),
      ]),
  );
  audit.append(auditTable);
  get("portfolio-table").append(audit);

  get("portfolio-assumptions").textContent = value.assumptions;
  const canvas = get("portfolio-chart");
  canvas.width = 900;
  canvas.height = 300;
  const context = canvas.getContext("2d"),
    values = [...value.equity, ...value.gross_equity],
    low = Math.min(...values),
    high = Math.max(...values),
    range = high - low || 1;
  context.clearRect(0, 0, 900, 300);
  [value.equity, value.gross_equity].forEach((series, j) => {
    context.strokeStyle = j ? "#447bb8" : "#167665";
    context.beginPath();
    series.forEach((v, i) => {
      const x = 60 + (i / (series.length - 1)) * 780,
        y = 250 - ((v - low) / range) * 210;
      if (i === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    });
    context.stroke();
  });
  context.font = "14px system-ui";
  context.fillStyle = "#167665";
  context.fillText("Net equity", 60, 285);
  context.fillStyle = "#447bb8";
  context.fillText("Gross equity", 260, 285);
}

(function () {
  const get = (id) => document.getElementById(id);
  let generation = 0,
    report = null;
  function invalidate() {
    generation++;
    report = null;
    get("portfolio" + "-results").hidden = true;
    get("portfolio" + "-export").disabled = true;
  }
  function save() {
    if (report) download("portfolio" + "-report.json", report);
  }
  get("portfolio" + "-export").onclick = save;
  async function execute(request) {
    invalidate();
    const token = generation;
    get("portfolio" + "-run").disabled = true;
    get("portfolio" + "-status").textContent =
      "Running bounded local calculation…";
    try {
      const response = await fetch("/portfolio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      const value = await response.json();
      if (token !== generation) return;
      if (!response.ok)
        throw Error(
          Array.isArray(value.detail)
            ? value.detail.map((row) => row.msg).join("; ")
            : value.detail,
        );
      report = {
        version: "0.4.0",
        input: request,
        result: value,
        source: source,
      };
      renderPortfolio(value);
      get("portfolio" + "-results").hidden = false;
      get("portfolio" + "-export").disabled = false;
      get("portfolio" + "-status").textContent =
        "Calculation finished. Review assumptions before interpreting.";
    } catch (error) {
      if (token === generation)
        get("portfolio" + "-status").textContent = error.message;
    } finally {
      get("portfolio" + "-run").disabled = false;
    }
  }
  let parsed = null,
    source = "";
  function load(text, label) {
    invalidate();
    parsed = LabData.parseCSV(text);
    source = label;
    get("portfolio-source").textContent = label;
    table(get("portfolio-preview"), parsed.headers, parsed.rows.slice(0, 8));
    get("portfolio-weights").replaceChildren();
    parsed.headers.forEach((name) => {
      const label = element("label"),
        check = element("input"),
        weight = element("input");
      check.type = "checkbox";
      check.value = name;
      check.className = "asset-choice";
      check.checked = true;
      weight.type = "number";
      weight.min = "0";
      weight.max = "100";
      weight.value = String(100 / parsed.headers.length);
      weight.className = "asset-weight";
      weight.style.width = "100px";
      label.append(check, element("span", name + " target %"), weight);
      get("portfolio-weights").append(label);
    });
    get("portfolio-status").textContent =
      "Select price columns and set target weights totaling 100%.";
  }
  get("portfolio-sample").onclick = () =>
    load(
      "asset_A,asset_B\n100,100\n110,100\n110,110\n121,110\n121,121\n133.1,121\n133.1,133.1\n146.41,133.1\n",
      "Synthetic portfolio prices",
    );
  get("portfolio-file").onchange = async (event) => {
    invalidate();
    parsed = null;
    const token = generation;
    try {
      const file = event.target.files[0];
      if (!file || file.size > 2097152)
        throw Error("Choose a CSV up to 2 MiB.");
      const text = await file.text();
      if (token === generation)
        load(text, "Imported data; provenance unverified: " + file.name);
    } catch (error) {
      if (token === generation)
        get("portfolio-status").textContent = error.message;
    }
  };
  get("portfolio-panel").addEventListener("input", invalidate);
  get("portfolio-run").onclick = () => {
    try {
      if (!parsed) throw Error("Load synthetic prices or import CSV first.");
      const selections = Array.from(
        get("portfolio-weights").querySelectorAll("label"),
      )
        .filter((label) => label.querySelector(".asset-choice").checked)
        .map((label) => ({
          name: label.querySelector(".asset-choice").value,
          percent: label.querySelector(".asset-weight").value,
        }));
      execute(
        LabAdvanced.portfolioInput(parsed, selections, {
          rebalance_every: Number(get("portfolio-every").value),
          cost_bps: Number(get("portfolio-cost").value),
        }),
      );
    } catch (error) {
      invalidate();
      get("portfolio-status").textContent = error.message;
    }
  };
})();
