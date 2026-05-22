"""中间件测试"""
from fastapi.testclient import TestClient

import service.api as api_module
from service.session_store import SessionStore


def create_client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "sessions.db"

    monkeypatch.setattr(
        api_module,
        "get_session_store",
        lambda: SessionStore(db_path),
    )

    return TestClient(api_module.app)


def test_response_includes_request_id_header(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_response_uses_request_id_from_header(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)

    response = client.get(
        "/health",
        headers={"X-Request-ID": "test-request-id"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"


def test_error_response_includes_request_id(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)

    response = client.post(
        "/chat",
        json={"message": "   "},
        headers={"X-Request-ID": "error-request-id"},
    )

    assert response.status_code == 422

    body = response.json()
    assert body["ok"] is False
    assert body["error"]["request_id"] == "error-request-id"

def test_chat_stream_error_includes_request_id(tmp_path, monkeypatch):
    """sse空消息测试"""
    client = create_client(tmp_path, monkeypatch)

    with client.stream(
        "POST",
        "/chat/stream",
        json={"message": "   "},
        headers={"X-Request-ID": "stream-error-id"},
    ) as response:
        assert response.status_code == 200
        text = "".join(response.iter_text())

    assert "event: error" in text
    assert "stream-error-id" in text