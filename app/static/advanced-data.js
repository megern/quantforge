/* Validated research requests assembled from mapped CSV, without executable input. */
(function (global) {
  const data =
    typeof module !== "undefined" && module.exports
      ? require("./data.js")
      : global.LabData;
  function portfolioInput(parsed, selections, settings) {
    const names = selections.map((row) => row.name);
    if (
      names.length < 2 ||
      names.length > 10 ||
      new Set(names).size !== names.length
    )
      throw Error("Select 2–10 different price columns.");
    if (parsed.rows.length > 2000)
      throw Error("Portfolio engine accepts at most 2,000 price rows.");
    if (selections.some((row) => String(row.percent).trim() === ""))
      throw Error("Enter a numeric weight for each selected asset.");
    const weights = selections.map((row) => Number(row.percent) / 100);
    if (
      weights.some((w) => !Number.isFinite(w) || w < 0 || w > 1) ||
      Math.abs(weights.reduce((a, b) => a + b, 0) - 1) > 1e-9
    )
      throw Error("Long-only asset weights must sum to 100%.");
    const columns = names.map((name) => data.numericColumn(parsed, name));
    return {
      ...settings,
      asset_names: names,
      weights,
      prices: parsed.rows.map((_, i) => columns.map((column) => column[i])),
    };
  }
  const api = { portfolioInput };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else global.LabAdvanced = api;
})(typeof window === "undefined" ? globalThis : window);
