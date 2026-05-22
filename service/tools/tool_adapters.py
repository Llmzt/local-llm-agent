"""工具适配器：将结构化arguments传递给具体工具调用并执行"""

from typing import Any

from service.core.errors import ToolError
from service.tools.tool_router import ToolResult
#各工具的执行函数
from skill.knowledge import search_knowledge
from skill.knowledge_write import add_knowledge
from skill.time import get_current_time


#------------------------输入解析为标准工具参数格式------------------------
def parse_empty_arguments(user_input:str) -> dict[str,Any]:
    """无参数工具的规则输入解析"""
    return {}

def parse_knowledge_search_arguments(user_input:str)->dict[str,Any]:
    """知识库查询规则输入解析"""
    return {
        "query":user_input,
    }

def parse_knowledge_write_arguments(user_input:str)->dict[str,Any]:
    """知识库吸入规则输入解析"""
    return {
        "text":user_input,
    }

#---------------------------工具执行--------------------------
def run_time_tool(arguments:dict[str,Any])->ToolResult:
    """执行工具时间"""
    return ToolResult(
        content=get_current_time(),
        metadata={
            "tool":"time",
        },
    )

def run_knowledge_search_tool(arguments:dict[str,Any])->ToolResult:
    """执行知识库查询工具"""
    query = str(arguments.get("query","")).strip()
    if not query:
        raise ToolError(
            "empty knowldege search query",
            user_message="请提供要查询的关键词",
        )
    return ToolResult(
        content=search_knowledge(query),
        metadata={
            "tool":"knowledge_search",
            "query":query,
        }
    )

def run_knowledge_write_tool(arguments:dict[str,Any])->ToolResult:
    """执行知识库写入操作"""
    text = str(arguments.get("text","")).strip()

    if not text:
        title =str(arguments.get("title","")).strip()
        content = str(arguments.get("content","")).strip()
        keywords = str(arguments.get("keywords","")).strip()
        text = f"添加知识: {title} | {content} | {keywords}"

    if not text:
        raise ToolError(
            "empty knowledge write input",
            user_message="请提供要写入的知识内容",
        )
    
    return  ToolResult(
        content=add_knowledge(text),
        metadata={
            "tool":"knowledge_write",
        },
    )
