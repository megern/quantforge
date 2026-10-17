import pytest
from fastapi.testclient import TestClient
from app.main import app, Request, analyze


def test_benchmark_alignment_and_compounded_cost_impact():
    result = analyze(
        Request(prices=[100, 110, 121, 121], signals=[1, 1, 1, 0], cost_bps=100)
    )
    assert result["benchmark"]["equity"] == pytest.approx([1, 1.1, 1.21, 1.21])
    assert result["benchmark"]["total_return"] == pytest.approx(0.21)
    assert result["gross_total_return"] == pytest.approx(0.21)
    assert result["total_return"] == pytest.approx(0.199)
    assert result["period_turnover"] == [1, 0, 0]
    assert result["period_cost_fractions"] == [0.01, 0, 0]
    assert result["cost_impact_return_points"] == pytest.approx(0.011)
    assert result["net_minus_benchmark_return_points"] == pytest.approx(-0.011)
    assert "No entry" in result["benchmark"]["cost_assumptions"]


def test_cash_strategy_uses_same_price_periods_and_no_costs():
    response = TestClient(app).post(
        "/analyze",
        json={"prices": [100, 90, 81, 100], "signals": [0, 0, 0, 0], "cost_bps": 10},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["equity"] == [1, 1, 1, 1]
    assert result["benchmark"]["max_drawdown"] == pytest.approx(0.19)
    assert len(result["benchmark"]["period_returns"]) == len(result["net_returns"]) == 3
    assert result["cost_impact_return_points"] == 0


def test_zero_cost_strategy_equals_benchmark():
    result = analyze(Request(prices=[100, 110, 90, 120], signals=[1] * 4, cost_bps=0))
    assert result["equity"] == pytest.approx(result["benchmark"]["equity"])
    assert result["cost_impact_return_points"] == 0
    assert result["net_minus_benchmark_return_points"] == pytest.approx(0)
