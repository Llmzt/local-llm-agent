"""LLM 工具规划"""

import json
import unicodedata

from service.logger import get_logger
from service.llm import call_planner_llm
from service.tool_router import ToolPlan,ToolSpec

logger = get_logger(__name__)

#缓存模块,记录“调用工具“这个结果，减少llm planner次数
_PLAN_CACHE: dict[str, ToolPlan] = {}


PLANNER_SYSTEM_PROMPT = """
你是一个工具路由规划器。你不是聊天助手，不能回答用户问题。

你只能返回 JSON，不要输出 Markdown，不要输出解释，不要输出自然语言。

你需要判断用户问题是否应该调用工具。

返回格式只能是以下两种之一：

{"tool": "工具名", "input": "传给工具的输入"}
{"tool": null, "input": null}

规则：
1. 只有当工具明显有帮助时才选择工具。
2. 如果用户只是普通聊天、写作、解释、总结，返回 {"tool": null, "input": null}。
3. input 应该是工具真正需要处理的简洁文本。
4. 不要编造不存在的工具名。
5. 不要直接回答用户问题。
6. 不要使用工具列表之外的工具名。
""".strip()


def plan_tool_with_llm(user_input:str,tools:list[ToolSpec]) ->ToolPlan:
    """调用LLM，判断是否需要工具"""
    
    cache_key = build_cache_key(user_input,tools)
    cached_plan = _PLAN_CACHE.get(cache_key)
    if cached_plan is not None:
        logger.info("tool planner cache hit")
        return cached_plan
    
    messages = [
        {
            "role":"system",
            "content":build_planner_prompt(tools),
        },
        {
            "role":"user",
            "content":user_input,
        },
    ]

    try:
        raw_reply = call_planner_llm(messages)
    except Exception as exc:
        logger.warning("tool planner llm call failed: %s",exc)
        plan = ToolPlan(tool=None,input=None)
        _PLAN_CACHE[cache_key]=plan
        return plan                             #优雅降级/fallback
                                                #不raise错误也就不会挂agent，保证继续运行
    plan = parse_tool_plan(raw_reply)
    _PLAN_CACHE[cache_key] = plan
    return plan

def build_planner_prompt(tools:list[ToolSpec])->str:
    """构造工具规划提示词"""
    tool_lines = []
    for tool in tools:
        tool_lines.append(
            f"- name: {tool.name}\n"
            f"  description: {tool.description}\n"
            f"  input_schema: {tool.input_schema}"
        )
    return(
        PLANNER_SYSTEM_PROMPT + "\n\n可用工具：\n" + "\n".join(tool_lines)
    )

def parse_tool_plan(raw_reply:str)->ToolPlan:
    """解析LLM返回的工具规划json"""
    text = raw_reply.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("tool planner returned invalid json: %s",raw_reply)
        return ToolPlan(tool=None,input=None)
    
    tool = data.get("tool")
    tool_input = data.get("input")

    if tool is not None and not isinstance(tool,str):#模型输出校验：大模型输出内容不完全可信，可能产生类型漂移
        return ToolPlan(tool=None,input=None)
    
    if tool_input is not None and not isinstance(tool_input,str):
        return ToolPlan(tool=None,input=None)
    
    return ToolPlan(tool=tool,input=tool_input)


def build_cache_key(user_input:str,tools:list[ToolSpec])->str:
    """工具函数：轻量级cache_key"""
    tool_names = ",".join(
    sorted(tool.name for tool in tools)
)
    normalized_input = normalize_user_input_for_cache(user_input)
    return f"{tool_names}:{normalized_input}"


def normalize_user_input_for_cache(user_input: str) -> str:
    """归一化用户输入，让大小写、全角、空白和标点不影响 planner 缓存。"""
    normalized = unicodedata.normalize("NFKC", user_input).casefold()
    return "".join(
        char
        for char in normalized
        if not char.isspace() and not unicodedata.category(char).startswith("P")
    )
