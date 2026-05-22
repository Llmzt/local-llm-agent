"""工具注册、规则路由和智能路由执行"""

from collections.abc import Callable
from dataclasses import dataclass

from service.logger import get_logger
from service.errors import ToolError

logger = get_logger(__name__)

@dataclass(frozen=True)
class ToolSpec:
    """agent可调用工具规范"""

    name:str
    description:str
    input_schema:str
    match:Callable[[str],bool]#函数[输入参数，返回值]
    handler: Callable[[str],str]#函数

@dataclass(frozen=True)
class ToolPlan:
    """LLM输出的工具计划"""
    tool: str|None
    input:str|None

def route_tool_by_rule(user_input: str, tools: list[ToolSpec]) ->str | None:
    """按顺序匹配工具，成功则执行，否则返回none。"""
    for tool in tools:
        if tool.match(user_input):
            logger.info("tool matched: name=%s",tool.name)
            return execute_tool(tool,user_input)
    
    logger.info("no tool matched")
    return None

def find_tool(tools:list[ToolSpec],name:str)->ToolSpec|None:
    """辅助函数：按名称查找工具"""
    for tool in tools:
        if tool.name == name:
            return tool
    return None

def execute_tool(tool:ToolSpec, tool_input:str) ->str:#tool_input：传给工具的参数
    """封装执行工具并统一包装工具异常"""
    try:
        return tool.handler(tool_input)
    except ToolError:#已知的可预期业务异常，直接raise，防止二次包装
                    #api可捕获异常类型自动写日志
        raise
    except Exception as exc:#工具调用业务内未知异常，包装为toolerror
                            #未知错误，raise后api不知道异常类型，需要手动记录现场
        logger.exception("tool execution failed: name=%s",tool.name)
        raise ToolError(
            f"tool execution failed:{tool.name}:{exc}",
            user_message=f"工具{tool.name}执行失败",
        )from exc

def execute_tool_plan(plan: ToolPlan,tools:list[ToolSpec])->str|None:
    """执行LLM生成的工具计划"""
    if plan.tool is None:
        logger.info("llm planner decided no tool")
        return None
    
    tool = find_tool(tools,plan.tool)
    if tool is None:#大模型给出工具，但不在工具列表里
        logger.warning("llm pannner returned unknown tool: %s",plan.tool)
        return None
    
    tool_input = plan.input or ""
    logger.info("tool mached by planner: name=%s",tool.name)
    return execute_tool(tool,tool_input)
