"""会话历史持久化：多轮对话保存到sqlite"""

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from service.errors import AppError
from service.env import PROJECT_ROOT
from service.sqlite_store import SQLiteStore

DEFAULT_SESSION_DB_PATH = PROJECT_ROOT / "database" / "sessions.db"

class SessionError(AppError):
    """会话存储相关异常"""

    user_message = "会话读写失败，请稍后再试。"

@dataclass(frozen=True)
class SessionMessage:
    id:int
    session_id: str
    role: str
    content:str
    created_at:str

class SessionStore(SQLiteStore):
    """SQLITE会话存储"""

    def __init__(self, db_path: Path | str = DEFAULT_SESSION_DB_PATH):
        super().__init__(db_path)

    def create_session(self) -> str:
        """创建新对话，返回 session_id"""
        session_id = uuid.uuid4().hex
        now = current_time_text()

        try:
            with self.transaction() as conn:
                self.ensure_tables(conn)
                conn.execute(
                    """
                    INSERT INTO sessions (id, created_at, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, now, now),
                )
        except sqlite3.Error as exc:
            raise SessionError(
                f"create session failed: {exc}",
                user_message="创建对话失败。"
            )from exc
        return session_id
    
    def ensure_session(self, session_id:str | None) ->str:
        """没有session_id时创建新对话，有session_id时保证其存在"""
        if not session_id:
            return self.create_session()
        
        try:
            with self.transaction() as conn:
                self.ensure_tables(conn)
                row = conn.execute(
                    "SELECT id FROM sessions WHERE id = ?",
                    (session_id,),
                ).fetchone()

                if row is None:#session_id不存在时
                    now = current_time_text()
                    conn.execute(
                        """
                        INSERT INTO sessions (id, created_at, updated_at)
                        VALUES (?, ?, ?)
                        """,
                        (session_id, now, now),
                    )
        except sqlite3.Error as exc:
            raise SessionError(
                f"ensure session failed:{exc}",
                user_message="初始化对话失败。",
            )from exc
        
        return session_id
    
    def get_history(self, session_id:str) ->list[dict[str,str]]:
        """读取某个历史对话，不包含system promt"""
        try:
            with self.connection() as conn:
                self.ensure_tables(conn)
                rows = conn.execute(
                    """
                    SELECT role, content
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY id
                    """,
                    (session_id,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise SessionError(
                f"get history failed:{exc}",
                user_message="读取历史对话失败",
            )from exc
        
        return [{"role": row["role"],"content":row["content"]}for row in rows]
    
    def append_message(self,session_id: str, role:str,content:str) ->None:
        """追加一条消息"""
        if role not in {"user","assistant"}:
            raise SessionError(
                f"invalid message role:{role}",
                user_message="角色不合法",
            )
        
        content = content.strip()
        if not content:
            raise SessionError(
                "empty message content",
                user_message="消息内容不能为空。",
            )
        
        now = current_time_text()

        try:
            with self.transaction() as conn:
                self.ensure_tables(conn)
                conn.execute(
                    """
                    INSERT INTO messages (session_id, role, content, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, role, content, now),
                )
                conn.execute(
                    """
                    UPDATE sessions
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (now, session_id),
                )
        except sqlite3.Error as exc:
            raise SessionError(
                f"append message failed:{exc}",
                user_message="保存会话消息失败"
            )from exc
    
    def ensure_tables(self, conn)->None:
        """确保会话表和消息表都存在"""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user','assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
            """
        )

    def delete_session(self,session_id:str)->bool:
        """删除对话，关联message由数据库级联删除"""
        try:
            with self.transaction() as conn:
                self.ensure_tables(conn)
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE id = ?",
                    (session_id,),
                )
        except sqlite3.Error as exc:
            raise SessionError(
                f"delete session failed:{exc}",
                user_message="删除对话失败."
            )from exc
        
        return cursor.rowcount>0 #判断删除操作生效与否

def current_time_text()->str:
    """返回适合数据库保存的时间文本"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")