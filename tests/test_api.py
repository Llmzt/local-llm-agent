"""集成测试FASTAPI"""
from fastapi.testclient import TestClient

from service.api import app

client = TestClient(app)

def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_with_time_tool():
    response = client.post(
        "/chat",
        json={"message": "现在几点？"},
    )

    assert response.status_code == 200

    data = response.json()
    assert "reply" in data
    assert "session_id" in data
    assert "history" in data
    assert len(data["reply"]) == 19
    assert data["history"][-1]["role"] == "assistant"

def test_chat_reuses_session_id():
    """确认历史对话"""
    first = client.post(
        "/chat",
        json={"message": "现在几点？"},
    )

    session_id = first.json()["session_id"]

    second = client.post(
        "/chat",
        json={
            "message": "今天日期？",
            "session_id": session_id,
        },
    )

    assert second.status_code == 200

    data = second.json()
    assert data["session_id"] == session_id
    assert len(data["history"]) >= 5