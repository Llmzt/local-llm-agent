"""SQLite 存储基础工具"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class SQLiteStore:
    """sqlite 数据访问基类"""

    def __init__(self,db_path:Path |str):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        """创建sqlite连接"""
        self.db_path.parent.mkdir(parents = True,exist_ok = True)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")#为每个连接单独启动外键约束检查,方便索引查找，防止脏数据库、数据残留、Dos等
    
        return conn


    #-----------数据访问规范化------------
    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """打开连接；适合只读查询。"""
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager#被装饰函数必须返回生成器
    def transaction(self) ->Iterator[sqlite3.Connection]:
        """开启事务；成功提交，失败则回滚"""
        #保证原子性
        conn = self.connect()
        try:
            yield conn#自动化connect、commit、rollback、close
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally :
            conn.close()