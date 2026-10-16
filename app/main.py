import math
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field, model_validator


def finite(values):
    if not all(abs(v) <= 1e100 and math.isfinite(v) for v in values):
        raise ValueError("numeric values must be finite with magnitude at most 1e100")


def matrix(rows):
    if (
        not rows
        or not rows[0]
        or len(rows[0]) > 50
        or any(len(row) != len(rows[0]) for row in rows)
    ):
        raise ValueError("numeric matrix must be rectangular with 1 to 50 columns")
    finite([v for row in rows for v in row])


class Request(BaseModel):
    prices: list[float] = Field(min_length=4, max_length=100000)
    signals: list[float] = Field(min_length=4, max_length=100000)
    cost_bps: float = Field(default=5, ge=0, le=1000)
    periods_per_year: int = Field(default=252, ge=1, le=100000)

    @model_validator(mode="after")
    def valid(self):
        finite(self.prices + self.signals)
        if len(self.prices) != len(self.signals) or min(self.prices) <= 0:
            raise ValueError(
                "prices and signals must have equal lengths; prices must be positive"
            )
        if max(abs(x) for x in self.signals) > 1:
            raise ValueError("signals must be between -1 and 1")
        return self


def analyze(req: Request):
    prices, signals = np.asarray(req.prices), np.asarray(req.signals)
    returns = prices[1:] / prices[:-1] - 1
    positions = signals[:-1]  # Only previously available signals are traded.
    turnover = np.abs(np.diff(np.r_[0.0, positions]))
    costs = turnover * req.cost_bps / 10000
    net = positions * returns - costs
    if np.any(net <= -1):
        raise ValueError("strategy equity is exhausted; reduce costs or exposure")
    equity = np.r_[1.0, np.cumprod(1 + net)]
    drawdown = equity / np.maximum.accumulate(equity) - 1
    volatility = float(np.std(net, ddof=1))
    return {
        "equity": equity.tolist(),
        "net_returns": net.tolist(),
        "positions": positions.tolist(),
        "turnover": float(turnover.sum()),
        "total_cost_fraction": float(costs.sum()),
        "total_return": float(equity[-1] - 1),
        "max_drawdown": float(-drawdown.min()),
        "sharpe": (
            float(np.mean(net) / volatility * np.sqrt(req.periods_per_year))
            if volatility > 1e-12
            else None
        ),
        "assumptions": "Signals at t affect return t to t+1. Fractional long/short exposure; no financing, slippage beyond stated costs, or liquidation cost. Sharpe assumes zero risk-free rate.",
    }


app = FastAPI(title="QuantForge", version="0.2.0")


STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/guide")
def user_guide():
    return FileResponse(
        Path(__file__).parent / "USER_GUIDE.md", media_type="text/plain"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def run_analysis(req: Request):
    try:
        result = analyze(req)

        def check(value):
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("numeric overflow; rescale input values")
            if isinstance(value, dict):
                for item in value.values():
                    check(item)
            elif isinstance(value, list):
                for item in value:
                    check(item)

        check(result)
        return result
    except (ValueError, np.linalg.LinAlgError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


from .guard import InputGuard

app.add_middleware(InputGuard)
