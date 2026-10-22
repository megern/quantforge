"""Independent accounting and timing review; all datasets are synthetic."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_manual_pro_rata_fee_rebalance_and_asset_accounting():
    r = client.post(
        "/portfolio",
        json={
            "prices": [[100, 100], [120, 80], [150, 100]],
            "asset_names": ["A", "B"],
            "weights": [0.5, 0.5],
            "rebalance_every": 1,
            "cost_bps": 100,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["equity"] == pytest.approx([0.99, 0.98802, 1.235025])
    assert data["gross_equity"] == pytest.approx([1, 1, 1.25])
    assert data["total_cost_in_initial_capital_units"] == pytest.approx(0.01198)
    assert data["total_turnover"] == pytest.approx(1.2)
    assert data["periods"][0]["pre_rebalance_weights"] == pytest.approx([0.6, 0.4])
    assert data["periods"][0]["rebalance"] and not data["periods"][1]["rebalance"]
    gains = [
        row["gain_in_initial_capital_units"] for row in data["asset_contributions"]
    ]
    assert gains == pytest.approx([0.2225025, 0.0245025])
    assert sum(gains) - data["total_cost_in_initial_capital_units"] == pytest.approx(
        data["equity"][-1] - 1
    )
    assert data["max_drawdown"] == pytest.approx(0.01198)


def test_buy_and_hold_versus_rebalanced_and_future_row_no_lookahead():
    base = {
        "prices": [[100, 100], [200, 50], [100, 100]],
        "asset_names": ["A", "B"],
        "weights": [0.5, 0.5],
        "cost_bps": 0,
    }
    held = client.post("/portfolio", json={**base, "rebalance_every": 100}).json()
    rebalanced = client.post("/portfolio", json={**base, "rebalance_every": 1}).json()
    assert held["equity"][-1] == pytest.approx(1)
    assert rebalanced["equity"][-1] == pytest.approx(1.5625)
    changed = client.post(
        "/portfolio",
        json={
            **base,
            "prices": [[100, 100], [200, 50], [500, 10]],
            "rebalance_every": 1,
        },
    ).json()
    assert changed["periods"][0] == rebalanced["periods"][0]


def test_zero_weight_constant_asset_has_no_gain_and_undefined_correlation():
    r = client.post(
        "/portfolio",
        json={
            "prices": [[100, 100], [110, 100], [121, 100]],
            "asset_names": ["active", "constant"],
            "weights": [1, 0],
            "cost_bps": 0,
        },
    ).json()
    assert r["equity"][-1] == pytest.approx(1.21)
    assert r["asset_contributions"][1]["gain_in_initial_capital_units"] == 0
    assert r["correlation"][1] == [None, None] and r["correlation"][0][1] is None
