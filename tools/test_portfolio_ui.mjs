import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import test from "node:test";
import { documentFromHTML, deferred } from "./ui-test-dom.mjs";

const staticRoot = new URL("../app/static/", import.meta.url);
const result = {
  total_return: 0.1,
  max_drawdown: 0.02,
  initial_allocation_cost: 0.0005,
  total_cost_in_initial_capital_units: 0.001,
  total_turnover: 1.1,
  asset_names: ["asset_A", "asset_B"],
  asset_contributions: [
    { asset: "asset_A", gain_in_initial_capital_units: 0.06 },
    { asset: "asset_B", gain_in_initial_capital_units: 0.041 },
  ],
  correlation: [
    [1, 0.2],
    [0.2, 1],
  ],
  periods: [
    {
      end_row_index: 1,
      rebalance: true,
      turnover: 0.1,
      cost_in_initial_capital_units: 0.0005,
      starting_weights: [0.5, 0.5],
      pre_rebalance_weights: [0.52, 0.48],
      net_equity: 1.04,
    },
  ],
  equity: [0.9995, 1.04, 1.1],
  gross_equity: [1, 1.041, 1.101],
  assumptions:
    "Synthetic response fixture; target weights apply before next return.",
};

function harness(
  responsePromise = Promise.resolve({ ok: true, json: async () => result }),
) {
  const document = documentFromHTML(
    fs.readFileSync(new URL("index.html", staticRoot), "utf8"),
  );
  const createElement = document.createElement;
  document.createElement = (tag) => {
    const node = createElement(tag);
    node.style = {};
    node.classList.toggle = () => {};
    return node;
  };
  for (const id of ["status", "portfolio-status"])
    document.getElementById(id).classList.toggle = () => {};
  const paths = [],
    labels = [],
    requests = [],
    blobs = [];
  document.getElementById("portfolio-chart").getContext = () => ({
    clearRect: () => {},
    beginPath: () => {},
    moveTo: (...p) => paths.push(p),
    lineTo: (...p) => paths.push(p),
    stroke: () => {},
    fillText: (text) => labels.push(text),
  });
  const context = {
    document,
    console,
    TextEncoder,
    Blob,
    setTimeout: () => {},
    URL: {
      createObjectURL: (blob) => {
        blobs.push(blob);
        return "blob:synthetic";
      },
      revokeObjectURL: () => {},
    },
    fetch: async (path, options) => {
      requests.push({ path, input: JSON.parse(options.body) });
      return responsePromise;
    },
  };
  context.window = context;
  vm.createContext(context);
  for (const file of [
    "config.js",
    "data.js",
    "advanced-data.js",
    "workbench.js",
    "advanced-ui.js",
  ])
    vm.runInContext(
      fs.readFileSync(new URL(file, staticRoot), "utf8"),
      context,
      { filename: file },
    );
  return { document, paths, labels, requests, blobs };
}
const flush = () => new Promise((resolve) => setImmediate(resolve));

test("actual synthetic-load/run handlers render portfolio, graph, audit and export", async () => {
  const h = harness(),
    get = (id) => h.document.getElementById(id);
  get("portfolio-sample").click();
  assert.equal(
    get("portfolio-source").textContent,
    "Synthetic portfolio prices",
  );
  assert.equal(get("portfolio-weights").querySelectorAll("label").length, 2);
  get("portfolio-run").click();
  await flush();
  assert.equal(h.requests.length, 1);
  assert.equal(h.requests[0].path, "/portfolio");
  assert.deepEqual(h.requests[0].input.weights, [0.5, 0.5]);
  assert.equal(h.requests[0].input.prices.length, 8);
  assert.equal(
    get("portfolio-results").hidden,
    false,
    get("portfolio-status").textContent,
  );
  assert.match(get("portfolio-status").textContent, /Calculation finished/);
  assert.match(get("portfolio-table").textContent, /Net return10%/);
  assert.match(get("portfolio-table").textContent, /Rebalance audit/);
  assert.match(get("portfolio-table").textContent, /Return correlation/);
  assert.equal(get("portfolio-assumptions").textContent, result.assumptions);
  assert.equal(h.paths.length, 6);
  assert.ok(h.paths.every((point) => point.every(Number.isFinite)));
  assert.deepEqual(h.labels, ["Net equity", "Gross equity"]);
  assert.equal(get("portfolio-export").disabled, false);
  get("portfolio-export").click();
  const exported = JSON.parse(await h.blobs[0].text());
  assert.equal(exported.version, "0.4.0");
  assert.equal(exported.source, "Synthetic portfolio prices");
  assert.deepEqual(exported.input, h.requests[0].input);
  assert.equal(exported.result.total_return, 0.1);
});

test("actual portfolio handler discards a response when controls change in flight", async () => {
  const pending = deferred(),
    h = harness(pending.promise),
    get = (id) => h.document.getElementById(id);
  get("portfolio-sample").click();
  get("portfolio-run").click();
  get("portfolio-panel").dispatch("input");
  pending.resolve({ ok: true, json: async () => result });
  await flush();
  assert.equal(get("portfolio-results").hidden, true);
  assert.equal(get("portfolio-export").disabled, true);
  assert.equal(h.paths.length, 0);
});
