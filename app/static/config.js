window.APP_CONFIG = {
  "title": "QuantForge",
  "subtitle": "Turn lagged research signals into an auditable backtest.",
  "question": "How did this exposure rule perform after turnover costs?",
  "action": "Run backtest",
  "mapping": [
    ["prices", "Price column"],
    ["signals", "Exposure signal (−1 to 1)"]
  ],
  "params": [
    ["cost_bps", "Turnover cost (basis points)", 5, 0, 1000],
    ["periods_per_year", "Periods per year", 252, 1, 100000]
  ],
  "note":
    "Rows must be chronological. A signal at row t is applied to the next price return. No trade execution or financial transactions.",
  "sample":
    "prices,signals\n95.5,1\n97.291,1\n99.0919,1\n100.9027,1\n102.7235,1\n104.5543,1\n106.3952,1\n97.5236,1\n99.3526,0\n101.1916,0\n103.0408,0\n104.9002,0\n106.7698,1\n108.6497,1\n99.5902,1\n101.4579,1\n103.3359,1\n105.2243,1\n107.123,1\n109.0322,1\n110.952,0\n101.7005,0\n103.6078,0\n105.5256,0\n107.454,1\n109.393,1\n111.3426,1\n113.303,1\n103.8555,1\n105.8032,1\n107.7616,1\n109.7309,1\n111.711,0\n113.702,0\n115.7039,0\n106.0562,0\n108.0452,1\n110.0451,1\n112.0561,1\n114.0781,1\n116.1113,1\n118.1557,1\n108.3035,1\n110.3346,1\n112.377,0\n114.4306,0\n116.4954,0\n118.5717,0\n",
  "slug": "quantforge"
};
