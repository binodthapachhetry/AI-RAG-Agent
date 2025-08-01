from fastapi.testclient import TestClient

from ai_rag_agent.app.factory import create_app


def test_echo_roundtrip():
    client = TestClient(create_app())
    payload = {"message": "hello"}
    r = client.post("/echo", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "hello"
    assert "received_at" in body
