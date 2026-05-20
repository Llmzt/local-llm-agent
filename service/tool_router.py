"""工具注册与路由"""

from collections.abc import Callable
from dataclasses import dataclass

from service.logger import get_logger

logger = get_logger(__name__)

@dataclass(frozen=True)
class Tool:
    name:str
    description: str
    match: Callable[[str], bool]
    handler: Callable[[str], str]

def route_tool(user_input: str, tools: list[Tool]) ->str | None:
    """按顺序匹配工具，成功则执行，否则返回none。"""
    for tool in tools:
        if tool.match(user_input):
            logger.info("tool matched: name=%s",tool.name)
            return tool.handler(user_input)
    
    logger.info("no tool matched")
    return None