from fastapi.testclient import TestClient

from ai_rag_agent.app.factory import create_app


def test_answer_non_streaming_json():
    client = TestClient(create_app())
    r = client.post("/v1/answer", params={"stream": "false"}, json={"query": "test"})
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body
    assert isinstance(body["citations"], list)


def test_answer_streaming_text():
    client = TestClient(create_app())
    with client.stream("POST", "/v1/answer?stream=true", json={"query": "test"}) as r:
        assert r.status_code == 200
        buf = b"".join(r.iter_bytes())
        assert b"placeholder answer" in buf
