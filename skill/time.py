"""时间工具。"""

from datetime import datetime


def get_current_time() -> str:
    """返回当前本地时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
