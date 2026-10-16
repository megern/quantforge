import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import Request, analyze, app


def test_lag_and_costs():
    result = analyze(
        Request(prices=[100, 110, 121, 121], signals=[0, 1, 1, 0], cost_bps=100)
    )
    assert result["positions"] == [0, 1, 1]
    assert result["net_returns"] == pytest.approx([0, 0.09, 0])
    assert result["equity"][-1] == pytest.approx(1.09)
    assert result["turnover"] == 1


def test_drawdown_and_constant():
    assert analyze(Request(prices=[100, 90, 81, 81], signals=[1, 1, 1, 1], cost_bps=0))[
        "max_drawdown"
    ] == pytest.approx(0.19)
    assert analyze(Request(prices=[1, 1, 1, 1], signals=[0, 0, 0, 0]))["sharpe"] is None


def test_api_and_ui():
    import json
    from pathlib import Path

    client = TestClient(app)
    payload = json.loads(
        (Path(__file__).parents[1] / "examples/synthetic.json").read_text()
    )
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), dict)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200
    assert client.post("/analyze", json={}).status_code == 422


def test_nonfinite_rejected():
    import json
    from pathlib import Path

    payload = json.loads(
        (Path(__file__).parents[1] / "examples/synthetic.json").read_text()
    )
    key = next(iter(payload))
    if isinstance(payload[key][0], list):
        payload[key][0][0] = "nan"
    else:
        payload[key][0] = "nan"
    assert TestClient(app).post("/analyze", json=payload).status_code == 422


def test_final_signal_does_not_affect_history():
    a = analyze(Request(prices=[100, 110, 120, 130], signals=[1, 1, 1, -1]))
    b = analyze(Request(prices=[100, 110, 120, 130], signals=[1, 1, 1, 1]))
    assert a["equity"] == b["equity"]


def test_invalid_lengths_prices_and_exposure():
    from pydantic import ValidationError

    for prices, signals in [
        ([0, 1, 2, 3], [0] * 4),
        ([1, 2, 3, 4], [0] * 5),
        ([1, 2, 3, 4], [2] * 4),
    ]:
        with pytest.raises(ValidationError):
            Request(prices=prices, signals=signals)


def test_bankruptcy_rejected():
    with pytest.raises(ValueError, match="exhausted"):
        analyze(Request(prices=[1, 3, 4, 5], signals=[-1] * 4))
