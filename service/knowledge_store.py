"""SQLite 知识库数据层：建表和查询。"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from service.errors import KnowledgeError

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "database" / "knowledge.db"


@dataclass(frozen=True)
class KnowledgeItem:
    id: int
    title: str
    content: str
    keywords: str


class KnowledgeStore:
    """最小 SQLite 数据访问对象。"""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)

    def search(self, query: str, limit: int = 3) -> list[KnowledgeItem]:
        """按标题、正文、关键词模糊查询知识。"""
        try:
            with self.connect() as conn:
                self.ensure_table(conn)
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
    def connect(self) -> sqlite3.Connection:
        """连接数据库；如果目录不存在就创建目录。"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def ensure_table(self, conn: sqlite3.Connection) -> None:
        """保证知识表存在。"""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                keywords TEXT
            )
            """
        )

    def row_to_item(self, row) -> KnowledgeItem:
        """把 SQLite 行转换成 KnowledgeItem。"""
        return KnowledgeItem(
            id=int(row[0]),
            title=str(row[1]),
            content=str(row[2]),
            keywords=str(row[3] or ""),
        )

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
            with self.connect() as conn:
                self.ensure_table(conn)
                cursor = conn.execute(
                    """
                    INSERT INTO knowledge (title, content, keywords)
                    VALUES (?, ?, ?)
                    """,
                    (title, content, keywords),
                )
                conn.commit()
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