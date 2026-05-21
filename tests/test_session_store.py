from service.session_store import SessionStore


def test_create_session_returns_session_id(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")

    session_id = store.create_session()

    assert isinstance(session_id, str)
    assert len(session_id) > 0


def test_append_and_get_history(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    session_id = store.create_session()

    store.append_message(session_id, "user", "你好")
    store.append_message(session_id, "assistant", "你好，有什么可以帮你？")

    history = store.get_history(session_id)

    assert history == [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
    ]


def test_ensure_session_creates_when_missing(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")

    session_id = store.ensure_session(None)

    assert isinstance(session_id, str)
    assert store.get_history(session_id) == []


def test_ensure_session_accepts_existing_id(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    session_id = "test-session"

    result = store.ensure_session(session_id)

    assert result == session_id
    assert store.get_history(session_id) == []


def test_delete_session_cascades_messages(tmp_path):
    """删除测试"""
    store = SessionStore(tmp_path / "sessions.db")
    session_id = store.create_session()

    store.append_message(session_id, "user", "你好")
    store.append_message(session_id, "assistant", "你好，有什么可以帮你？")

    deleted = store.delete_session(session_id)

    assert deleted is True

    with store.connect() as conn:
        rows = conn.execute(
            "SELECT id FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchall()

    assert rows == []

def test_delete_session_returns_false_when_missing(tmp_path):
    """删除失败测试"""
    store = SessionStore(tmp_path / "sessions.db")

    deleted = store.delete_session("missing-session")

    assert deleted is False

def test_session_exists(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    session_id = store.create_session()

    assert store.session_exists(session_id) is True
    assert store.session_exists("missing-session") is False