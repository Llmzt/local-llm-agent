"""测试FASTAPI"""
from fastapi.testclient import TestClient

import service.api as api_module
from service.session_store import SessionStore


def create_client(tmp_path, monkeypatch)->TestClient:
    """使用临时session数据库进行api测试"""
    db_path = tmp_path / "session.db"

    monkeypatch.setattr(api_module,"get_session_store",lambda: SessionStore(db_path),)

    return TestClient(api_module.app)

def test_health(tmp_path,monkeypatch):
    client = create_client(tmp_path,monkeypatch)

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["ok"] is True
    assert data["data"] == {"status": "ok"}
    assert data["error"] is None

def test_chat_with_time_tool(tmp_path , monkeypatch):

    client = create_client(tmp_path,monkeypatch)

    response = client.post(
        "/chat",
        json={"message": "现在几点？"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["ok"] is True
    assert body["error"] is None

    data = body["data"]
    assert "reply" in data
    assert "session_id" in data
    assert "history" in data
    assert len(data["reply"]) == 19
    assert data["history"][-1]["role"] == "assistant"

def test_chat_reuses_session_id(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)

    first = client.post(
        "/chat",
        json={"message": "现在几点？"},
    )

    session_id = first.json()["data"]["session_id"]

    second = client.post(
        "/chat",
        json={
            "message": "今天日期？",
            "session_id": session_id,
        },
    )

    assert second.status_code == 200

    body = second.json()
    assert body["ok"] is True

    data = body["data"]
    assert data["session_id"] == session_id
    assert len(data["history"]) >= 5

def test_chat_rejects_blank_message(tmp_path, monkeypatch):
    """/chat 接口是否正确拒绝非法空消息请求"""
    client = create_client(tmp_path, monkeypatch)

    response = client.post(
        "/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422

    body = response.json()
    assert body["ok"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "HTTP_ERROR"


def test_get_session_history(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)

    first = client.post(
        "/chat",
        json={"message": "现在几点？"},
    )

    session_id = first.json()["data"]["session_id"]

    response = client.get(f"/sessions/{session_id}")

    assert response.status_code == 200

    body = response.json()
    assert body["ok"] is True
    assert body["data"]["session_id"] == session_id
    assert len(body["data"]["history"]) >= 2


def test_get_session_history_returns_404_when_missing(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)

    response = client.get("/sessions/missing-session")

    assert response.status_code == 404

    body = response.json()
    assert body["ok"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "HTTP_ERROR"