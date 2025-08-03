import time

from fastapi.testclient import TestClient

from ai_rag_agent.app.factory import create_app

client = TestClient(create_app())


def test_timeout_504():
    t0 = time.perf_counter()
    r = client.get("/v1/demo-timeout?mode=slow&sleep_ms=1000&timeout_ms=100")
    t1 = time.perf_counter()
    assert r.status_code == 504
    assert (t1 - t0) < 0.5  # fails fast


def test_retry_eventual_success():
    r = client.get("/v1/demo-retry?mode=fail_then_ok&fail_times=1&key=K")
    assert r.status_code == 200


def test_breaker_opens_and_half_opens():
    # two failures -> open
    client.get("/v1/demo-breaker?mode=fail")
    client.get("/v1/demo-breaker?mode=fail")
    r = client.get("/v1/demo-breaker?mode=ok")  # immediate 503 (open)
    assert r.status_code == 503
    # cooldown
    import time as _t

    _t.sleep(2.1)
    r2 = client.get("/v1/demo-breaker?mode=ok")
    assert r2.status_code == 200
