from fastapi.testclient import TestClient

from ai_rag_agent.app.factory import create_app


def test_metrics_exposed():
    client = TestClient(create_app())
    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "http_requests_total" in text or "http_request_duration_seconds" in text
