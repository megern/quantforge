import numpy as np
from fastapi.testclient import TestClient
from app.main import Request, analyze, app

def test_reviewer_hand_calculated_cost_and_lag():
    r=analyze(Request(prices=[100,110,99,108.9],signals=[1,-1,0,1],cost_bps=100))
    # Prior position earns each return; entering and reversing cost 1% and 2%.
    assert np.allclose(r['net_returns'],[.09,.08,-.01])
    assert np.allclose(r['equity'],[1,1.09,1.1772,1.165428])
    assert np.isclose(r['turnover'],4)
    assert np.isclose(r['max_drawdown'],.01)

def test_reviewer_final_signal_cannot_leak_into_returns():
    common={'prices':[100,110,99,108.9],'cost_bps':0}
    a=analyze(Request(**common,signals=[0,1,0,1]))
    b=analyze(Request(**common,signals=[0,1,0,-1]))
    assert a==b

def test_reviewer_invalid_extreme_and_bankruptcy_api():
    c=TestClient(app)
    assert c.post('/analyze',json={'prices':[100,200,100,100],'signals':[-1,-1,-1,-1]}).status_code==422
    assert c.post('/analyze',json={'prices':[1e-300,1e300,1e300,1e300],'signals':[1,1,1,1]}).status_code==422
