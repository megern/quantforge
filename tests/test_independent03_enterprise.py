"""Independent reviewer checks with synthetic, hand-computable financial arithmetic."""
import math
from statistics import mean, stdev
import pytest
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)


def test_independent_turnover_compounding_and_cost_free_benchmark():
    r=client.post('/analyze',json={'prices':[100,120,90,99],'signals':[1,-1,0.5,1],'cost_bps':10,'periods_per_year':12})
    assert r.status_code==200
    result=r.json()
    gross=[0.2,0.25,0.05]
    net=[0.199,0.248,0.0485]
    expected_gross=math.prod(1+x for x in gross)
    expected_net=math.prod(1+x for x in net)
    assert result['positions']==[1,-1,0.5]
    assert result['period_turnover']==[1,2,1.5]
    assert result['period_cost_fractions']==pytest.approx([0.001,0.002,0.0015])
    assert result['equity'][-1]==pytest.approx(expected_net)
    assert result['gross_equity'][-1]==pytest.approx(expected_gross)
    assert result['cost_impact_return_points']==pytest.approx(expected_gross-expected_net)
    assert result['benchmark']['equity']==pytest.approx([1,1.2,0.9,0.99])
    assert result['benchmark']['max_drawdown']==pytest.approx(0.25)
    assert result['benchmark']['total_return']==pytest.approx(-0.01)
    assert result['sharpe']==pytest.approx(mean(net)/stdev(net)*math.sqrt(12))
    assert result['net_minus_benchmark_return_points']==pytest.approx(expected_net-0.99)


def test_independent_unused_last_signal_does_not_change_attribution():
    data={'prices':[100,110,105,107],'signals':[0,1,-1,1],'cost_bps':5}
    first=client.post('/analyze',json=data).json();data['signals'][-1]=-1
    assert client.post('/analyze',json=data).json()==first


def test_extreme_ratio_yields_controlled_rejection_not_infinite_report():
    response=client.post('/analyze',json={'prices':[1e-300,1e100,1e-300,1e100],'signals':[1,1,1,1]})
    assert response.status_code==422
