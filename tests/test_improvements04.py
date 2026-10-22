import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_drift_turnover_initial_fee_and_pnl_reconcile():
    data = {
        "prices": [[100, 100], [120, 100], [120, 120]],
        "asset_names": ["a", "b"],
        "weights": [0.5, 0.5],
        "rebalance_every": 1,
        "cost_bps": 100,
    }
    response = TestClient(app).post("/portfolio", json=data)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["initial_allocation_cost"] == 0.01
    assert result["equity"][0] == 0.99
    assert result["periods"][0]["pre_rebalance_weights"] == pytest.approx(
        [6 / 11, 5 / 11]
    )
    assert result["periods"][0]["turnover"] == pytest.approx(1 / 11)
    assert result["periods"][1]["starting_weights"] == [0.5, 0.5]
    assert result["periods"][1]["rebalance"] is False
    assert result["equity"][-1] == pytest.approx((0.99 * 1.1) * (1 - 0.01 / 11) * 1.1)
    assert sum(
        row["gain_in_initial_capital_units"] for row in result["asset_contributions"]
    ) - result["total_cost_in_initial_capital_units"] == pytest.approx(
        result["total_return"]
    )


def test_unrebalanced_weights_are_lagged_and_drift():
    result = (
        TestClient(app)
        .post(
            "/portfolio",
            json={
                "prices": [[100, 100], [120, 100], [120, 120]],
                "asset_names": ["a", "b"],
                "weights": [0.5, 0.5],
                "rebalance_every": 10,
                "cost_bps": 0,
            },
        )
        .json()
    )
    assert result["equity"] == pytest.approx([1, 1.1, 1.2])
    assert result["periods"][1]["starting_weights"] == pytest.approx([6 / 11, 5 / 11])
    assert result["correlation"][0][1] == pytest.approx(-1)


@pytest.mark.parametrize("weights", [[0.5, 0.6], [-0.1, 1.1], [1]])
def test_bad_portfolio_weights(weights):
    response = TestClient(app).post(
        "/portfolio",
        json={"prices": [[1, 1]] * 3, "asset_names": ["a", "b"], "weights": weights},
    )
    assert response.status_code == 422


def test_documented_synthetic_feature_request_is_runnable():
    import json
    from pathlib import Path

    data = json.loads(
        (Path(__file__).parents[1] / "examples/synthetic-portfolio.json").read_text()
    )
    response = TestClient(app).post("/portfolio", json=data)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), dict)
