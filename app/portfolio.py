"""Long-only fixed-target portfolio research with explicit pro-rata fee funding."""

import math
import numpy as np
from pydantic import BaseModel, Field, model_validator


class PortfolioRequest(BaseModel):
    prices: list[list[float]] = Field(min_length=3, max_length=2000)
    asset_names: list[str] = Field(min_length=2, max_length=10)
    weights: list[float] = Field(min_length=2, max_length=10)
    rebalance_every: int = Field(default=5, ge=1, le=2000)
    cost_bps: float = Field(default=5, ge=0, le=1000, allow_inf_nan=False)

    @model_validator(mode="after")
    def valid(self):
        self.asset_names = [name.strip() for name in self.asset_names]
        width = len(self.asset_names)
        if len(set(self.asset_names)) != width or any(
            not n.strip() or len(n) > 80 for n in self.asset_names
        ):
            raise ValueError(
                "asset names must be unique nonempty strings up to 80 characters"
            )
        if len(self.weights) != width or any(len(r) != width for r in self.prices):
            raise ValueError("price matrix and weights must match asset names")
        if any(
            not math.isfinite(v) or v < 1e-12 or v > 1e12
            for r in self.prices
            for v in r
        ):
            raise ValueError("portfolio prices must be finite between 1e-12 and 1e12")
        if any(
            not math.isfinite(w) or w < 0 or w > 1 for w in self.weights
        ) or not math.isclose(sum(self.weights), 1, abs_tol=1e-9):
            raise ValueError("long-only target weights must sum to 1")
        return self


def analyze_portfolio(req):
    prices = np.asarray(req.prices)
    target = np.asarray(req.weights)
    rate = req.cost_bps / 10000
    returns = prices[1:] / prices[:-1] - 1
    initial_turnover = float(target.sum())
    initial_cost = initial_turnover * rate
    equity = [1 - initial_cost]
    gross_equity = [1.0]
    current = target.copy()
    contributions = np.zeros(len(target))
    costs = [initial_cost]
    turnovers = [initial_turnover]
    periods = []
    for index, asset_returns in enumerate(returns):
        starting_weights = current.copy()
        starting = equity[-1]
        gain = current * asset_returns
        factor = 1 + float(gain.sum())
        if factor <= 0 or not math.isfinite(factor):
            raise ValueError("invalid portfolio growth factor")
        contributions += starting * gain
        before_fee = starting * factor
        drift = current * (1 + asset_returns) / factor
        rebalance = (index + 1) % req.rebalance_every == 0 and index + 1 < len(returns)
        turnover = float(np.abs(target - drift).sum()) if rebalance else 0.0
        fee = before_fee * rate * turnover
        ending = before_fee - fee
        if not math.isfinite(ending) or ending <= 0:
            raise ValueError(
                "portfolio equity overflow/exhaustion; rescale extreme price paths"
            )
        current = target.copy() if rebalance else drift
        equity.append(ending)
        gross_equity.append(gross_equity[-1] * factor)
        if not math.isfinite(gross_equity[-1]):
            raise ValueError("gross equity overflow; reduce extreme price paths")
        costs.append(fee)
        turnovers.append(turnover)
        periods.append(
            {
                "end_row_index": index + 1,
                "starting_weights": starting_weights.tolist(),
                "pre_rebalance_weights": drift.tolist(),
                "rebalance": rebalance,
                "turnover": turnover,
                "cost_in_initial_capital_units": fee,
                "net_equity": ending,
            }
        )
    if not np.all(np.isfinite(contributions)) or not math.isfinite(sum(costs)):
        raise ValueError("portfolio accounting overflow; reduce extreme price paths")
    correlation = []
    for i in range(len(target)):
        row = []
        for j in range(len(target)):
            a, b = returns[:, i], returns[:, j]
            sa, sb = float(a.std()), float(b.std())
            row.append(
                float(
                    np.clip(
                        np.mean(((a - a.mean()) / sa) * ((b - b.mean()) / sb)), -1, 1
                    )
                )
                if sa > 0 and sb > 0
                else None
            )
        correlation.append(row)
    peak = np.maximum.accumulate(np.r_[1.0, equity])
    drawdown = 1 - np.r_[1.0, equity] / peak
    return {
        "asset_names": req.asset_names,
        "target_weights": req.weights,
        "equity": equity,
        "gross_equity": gross_equity,
        "initial_allocation_turnover": initial_turnover,
        "initial_allocation_cost": initial_cost,
        "total_turnover": sum(turnovers),
        "total_cost_in_initial_capital_units": sum(costs),
        "total_return": equity[-1] - 1,
        "max_drawdown": float(drawdown.max()),
        "asset_contributions": [
            {"asset": name, "gain_in_initial_capital_units": float(value)}
            for name, value in zip(req.asset_names, contributions)
        ],
        "correlation": correlation,
        "periods": periods,
        "assumptions": "Long-only fully invested fixed target. Initial allocation occurs at first row and costs L1 weight turnover × basis-point rate. Beginning weights earn the next price return; weights drift before scheduled end-period rebalancing. No terminal rebalance. Rebalance fees are paid pro rata from portfolio capital; additional fee-funding trades are excluded from turnover. Contributions are actual net-capital weighted price gains, so sum(contributions) minus total fees equals final equity minus initial capital. Gross equity follows identical drift/rebalance dates without fees. Correlation uses observed simple asset returns; constant-return pairs are null. No execution, financing, dividends, taxes or investment recommendation.",
    }
