from service.stores.session_store import SessionStore


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


def test_delete_session_supports_legacy_schema_without_cascade(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    session_id = "legacy-session"

    with store.transaction() as conn:
        conn.execute(
            """
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user','assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
            """
        )
        conn.execute(
            """
            INSERT INTO sessions (id, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (session_id, "2026-01-01 00:00:00", "2026-01-01 00:00:00"),
        )
        conn.execute(
            """
            INSERT INTO messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, "user", "你好", "2026-01-01 00:00:00"),
        )

    deleted = store.delete_session(session_id)

    assert deleted is True

    with store.connect() as conn:
        messages = conn.execute(
            "SELECT id FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchall()
        sessions = conn.execute(
            "SELECT id FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchall()

    assert messages == []
    assert sessions == []

def test_session_exists(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    session_id = store.create_session()

    assert store.session_exists(session_id) is True
    assert store.session_exists("missing-session") is False

def test_list_sessions(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    session_id = store.create_session()

    store.append_message(session_id, "user", "你好")
    store.append_message(session_id, "assistant", "你好，有什么可以帮你？")

    sessions = store.list_sessions()

    assert len(sessions) == 1
    assert sessions[0]["session_id"] == session_id
    assert sessions[0]["title"] == "你好"
    assert sessions[0]["message_count"] == 2
