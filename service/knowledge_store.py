"""SQLite 知识库数据层：建表、写入和查询。"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from service.env import PROJECT_ROOT
from service.sqlite_store import SQLiteStore
from service.errors import KnowledgeError

DEFAULT_DB_PATH = PROJECT_ROOT / "database" / "knowledge.db"


@dataclass(frozen=True)
class KnowledgeItem:
    id: int
    title: str
    content: str
    keywords: str


class KnowledgeStore(SQLiteStore):
    """知识库 SQLite 数据访问对象。"""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        super().__init__(db_path)#调用父类方法,对当前路径数据库公共属性进行初始化

    def search(self, query: str, limit: int = 3) -> list[KnowledgeItem]:
        """按标题、正文、关键词模糊查询知识。"""
        try:
            with self.transaction() as conn:
                self.ensure_tables(conn)
                rows = conn.execute(
                    """
                    SELECT id, title, content, keywords
                    FROM knowledge
                    WHERE title LIKE ?
                    OR content LIKE ?
                    OR keywords LIKE ?
                    ORDER BY id
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", f"%{query}%", limit),
                ).fetchall()
        except sqlite3.Error as exc:
            raise KnowledgeError(
                f"knowledge search failed: {exc}",
                user_message="查询知识库失败，请稍后重试。",
            ) from exc

        return [self.row_to_item(row) for row in rows]

    def add(self, title: str, content: str, keywords: str = "") -> KnowledgeItem:
        """新增一条知识，并返回写入后的 KnowledgeItem。"""
        title = title.strip()
        content = content.strip()
        keywords = keywords.strip()

        if not title:
            raise KnowledgeError("empty knowledge title", user_message="知识标题不能为空。")
        if not content:
            raise KnowledgeError("empty knowledge content", user_message="知识内容不能为空。")

        try:
            with self.transaction() as conn:
                self.ensure_tables(conn)
                cursor = conn.execute(
                    """
                    INSERT INTO knowledge (title, content, keywords)
                    VALUES (?, ?, ?)
                    """,
                    (title, content, keywords),
                )
                item_id = int(cursor.lastrowid)
        except sqlite3.Error as exc:
            raise KnowledgeError(
                f"knowledge add failed: {exc}",
                user_message="写入知识库失败，请稍后重试。",
            ) from exc

        return KnowledgeItem(
            id=item_id,
            title=title,
            content=content,
            keywords=keywords,
        )

    def ensure_tables(self, conn: sqlite3.Connection) -> None:
        """保证知识表存在。"""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                keywords TEXT NOT NULL DEFAULT ''
            )
            """
        )

    def row_to_item(self, row) -> KnowledgeItem:
        """把 SQLite 行转换成 KnowledgeItem。"""
        return KnowledgeItem(
            id=int(row["id"]),
            title=str(row["title"]),
            content=str(row["content"]),
            keywords=str(row["keywords"] or ""),
        )

    