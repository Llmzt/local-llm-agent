"""接口响应测试"""
from fastapi.testclient import TestClient

import service.api.api as api_module
from service.stores.session_store import SessionStore


def create_client(tmp_path, monkeypatch)->TestClient:
    """使用临时session数据库进行api测试"""
    db_path = tmp_path / "session.db"

    monkeypatch.setattr(api_module,"get_session_store",lambda: SessionStore(db_path),)
    monkeypatch.setattr(
        api_module,
        "run_agent",
        lambda messages, stream=True, stream_print=False: "2026-05-22 13:16:40",
    )
    monkeypatch.setattr(
        api_module,
        "run_agent_stream",
        lambda messages: iter(["2026-05-22 13:16:40"]),
    )

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
    """非sse非法空消息请求响应测试"""
    client = create_client(tmp_path, monkeypatch)

    response = client.post(
        "/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422

    body = response.json()
    assert body["ok"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "EMPTY_MESSAGE"
    assert body["error"]["message"] == "message 不能为空"


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

def test_list_sessions(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)

    first = client.post("/chat", json={"message": "现在几点？"})
    session_id = first.json()["data"]["session_id"]

    response = client.get("/sessions")

    assert response.status_code == 200

    body = response.json()
    assert body["ok"] is True
    assert body["data"]["sessions"][0]["session_id"] == session_id


def test_delete_session_api(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)

    first = client.post("/chat", json={"message": "现在几点？"})
    session_id = first.json()["data"]["session_id"]

    response = client.delete(f"/sessions/{session_id}")

    assert response.status_code == 200

    body = response.json()
    assert body["ok"] is True
    assert body["data"]["deleted"] is True

    missing = client.get(f"/sessions/{session_id}")
    assert missing.status_code == 404


def test_chat_stream_with_time_tool(tmp_path, monkeypatch):
    """测试时间工具（流式）"""
    client = create_client(tmp_path, monkeypatch)

    with client.stream(
        "POST",
        "/chat/stream",
        json={"message": "现在几点？"},
    ) as response:
        assert response.status_code == 200
        text = "".join(response.iter_text())

    assert "event: session" in text
    assert "event: chunk" in text
    assert "event: done" in text

def test_chat_stream_rejects_blank_message(tmp_path, monkeypatch):
    """SSE空消息测试"""
    client = create_client(tmp_path, monkeypatch)

    with client.stream(
        "POST",
        "/chat/stream",
        json={"message": "   "},
    ) as response:
        assert response.status_code == 200
        text = "".join(response.iter_text())

    assert "event: error" in text
    assert "EMPTY_MESSAGE" in text
    assert "message 不能为空" in text
