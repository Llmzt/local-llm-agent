"""工具注册、规则路由和智能路由执行"""

from collections.abc import Callable
from dataclasses import dataclass,field
from typing import Any

from service.core.logger import get_logger
from service.core.errors import ToolError

logger = get_logger(__name__)

#---------------------------结构规范-----------------------------

@dataclass(frozen=True)
class ToolResult:
    """工具执行结果规范结构"""

    content: str
    metadata: dict[str,Any] = field(default_factory=dict) #default_factory:[调用函数]时默认生成值


@dataclass(frozen=True)
class ToolSpec:
    """agent可调用工具规范结构"""

    name:str
    description:str
    arguments_schema:dict[str,Any]                      #工具参数规范描述
    match:Callable[[str],bool]                          #函数[输入参数，返回值]
    parse_rule_input:Callable[[str], dict[str, Any]]    #自然语言->规范化工具参数转换
    handler: Callable[[dict[str, Any]], ToolResult]
    side_effect: bool = False                           #是否有副作用：写操作、代理执行等
    planner_enabled: bool = True                        #是否可以自动被大模型调用（删库等危险工具必须人工决定）

@dataclass(frozen=True)
class ToolPlan:
    """LLM输出的工具计划"""
    tool: str|None
    arguments:dict[str,Any]|None = None


#--------------------工具调用函数-----------------------
def route_tool_by_rule(user_input: str, tools: list[ToolSpec]) ->ToolResult | None:
    """关键词匹配工具，成功则执行，否则返回none。"""
    for tool in tools:
        if tool.match(user_input):
            logger.info("tool matched by rule: name=%s",tool.name)
            arguments = tool.parse_rule_input(user_input)
            return execute_tool(tool,arguments)
    
    logger.info("no rule tool matched")
    return None

def find_tool(tools:list[ToolSpec],name:str)->ToolSpec|None:
    """辅助函数：按名称查找工具"""
    for tool in tools:
        if tool.name == name:
            return tool
    return None

def execute_tool(tool:ToolSpec, arguments:dict[str,Any]) ->ToolResult:
    """执行工具并统一处理工具异常"""
    try:
        return tool.handler(arguments)
    except ToolError:                   #已知的可预期业务异常，直接raise，防止二次包装
                                        #api可捕获异常类型自动写日志
        raise
    except Exception as exc:            #工具调用业务内未知异常，包装为toolerror
                                        #未知错误，raise后api不知道异常类型，需要手动记录现场
        logger.exception("tool execution failed: name=%s",tool.name)
        raise ToolError(
            f"tool execution failed:{tool.name}:{exc}",
            user_message=f"工具{tool.name}执行失败",
        )from exc

def execute_tool_plan(plan: ToolPlan,tools:list[ToolSpec])->ToolResult|None:
    """执行LLM生成的工具计划"""
    if plan.tool is None:
        logger.info("llm planner decided no tool")
        return None
    
    tool = find_tool(tools,plan.tool)
    if tool is None:                     #大模型给出工具，但不在工具列表里(可能是幻觉)
        logger.warning("llm pannner returned unknown tool: %s",plan.tool)
        return None
    
    if tool.side_effect and not tool.planner_enabled:
        logger.warning("planner tried to call disabled side-effect tool:%s",tool.name)
        return None
    
    arguments = plan.arguments or {}
    logger.info("tool mached by planner: name=%s",tool.name)
    return execute_tool(tool,arguments)
