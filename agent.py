"""Agent 主流程：决定走本地工具，还是交给普通 LLM。"""
from service.llm import stream_llm_chunks,call_llm_with_model,get_config
from skill.knowledge import search_knowledge    #用于隐式知识库查询
from service.tools.tool_adapters import (
    parse_empty_arguments,
    parse_knowledge_search_arguments,
    parse_knowledge_write_arguments,
    run_knowledge_search_tool,
    run_knowledge_write_tool,
    run_time_tool,
)
from service.core.logger import get_logger
from service.tools.tool_router import (
    ToolSpec,
    execute_tool_plan,
    route_tool_by_rule,
)
from service.tools.tool_planner import plan_tool_with_llm

from collections.abc import Iterator

logger = get_logger(__name__)

SYSTEM_PROMPT = "你是一个极简中文助手。请直接回答用户问题，不要输出多余解释。"

NO_KNOWLEDGE_RESULT = "没有找到相关知识。"
EMPTY_KNOWLEDGE_QUERY = "请提供要查询的关键词。"

TIME_WORDS = ("什么时间", "现在几点", "什么日期")
KNOWLEDGE_WORDS = ("知识库", "查询", "搜索", "检索")
ADD_KNOWLEDGE_WORDS = ("添加知识", "新增知识", "写入知识")


TOOLS = [
    ToolSpec(
        name="knowledge_write",
        description="把用户提供的标题、内容、关键词写入本地知识库。",
        arguments_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "原始写入指令，例如：添加知识：标题 | 内容 | 关键词",
                },
                "title": {
                    "type": "string",
                    "description": "知识标题",
                },
                "content": {
                    "type": "string",
                    "description": "知识正文",
                },
                "keywords": {
                    "type": "string",
                    "description": "关键词",
                },
            },
        },
        match=lambda text: any(word in text for word in ADD_KNOWLEDGE_WORDS),
        parse_rule_input=parse_knowledge_write_arguments,
        handler=run_knowledge_write_tool,
        side_effect=True,
        planner_enabled=False,
    ),
    ToolSpec(
        name="time",
        description="回答当前时间、日期、星期相关问题。",
        arguments_schema={
            "type": "object",
            "properties": {},
        },
        match=lambda text: any(word in text for word in TIME_WORDS),
        parse_rule_input=parse_empty_arguments,
        handler=run_time_tool,
        side_effect=False,
        planner_enabled=True,
    ),
    ToolSpec(
        name="knowledge_search",
        description="查询本地 SQLite 知识库，适合检索已有知识、资料、笔记。",
        arguments_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要查询的关键词或问题",
                },
            },
            "required": ["query"],
        },
        match=lambda text: any(word in text for word in KNOWLEDGE_WORDS),
        parse_rule_input=parse_knowledge_search_arguments,
        handler=run_knowledge_search_tool,
        side_effect=False,
        planner_enabled=True,
    ),
]

def run_planned_tool(user_input: str):
    """规则未命中时，让 LLM 判断是否需要工具。"""
    plan = plan_tool_with_llm(user_input, TOOLS)
    return execute_tool_plan(plan, TOOLS)

#---------------------多轮对话管理------------------------
def create_history() -> list[dict[str, str]]:
    """创建一段新对话。"""
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def trim_history(
    messages: list[dict[str, str]],
    max_rounds: int = 10,
) -> list[dict[str, str]]:
    """保留 system prompt 和最近几轮对话。"""
    system_message = messages[0]
    recent_messages = messages[1:][-max_rounds * 2 :]
    return [system_message] + recent_messages


def add_user_message(messages: list[dict[str, str]], text: str) -> None:
    """把用户输入加入历史。"""
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages: list[dict[str, str]], text: str) -> None:
    """把助手回复加入历史。"""
    messages.append({"role": "assistant", "content": text})


def run_agent(
    messages: list[dict[str, str]],
    stream: bool = True,
    stream_print: bool = False,
) -> str:
    """Agent 入口：用户输入 -> 工具判断 -> 返回结果。"""
    config = get_config()
    user_input = messages[-1]["content"]

    #关键词匹配   
    tool_result = route_tool_by_rule(user_input, TOOLS)
    if tool_result is not None:
        return reply_with_text(tool_result.content, stream_print)

    #大模型决策
    planned_result = run_planned_tool(user_input)
    if planned_result is not None:
        return reply_with_text(planned_result.content, stream_print)

    knowledge_reply = search_knowledge(user_input)#隐式知识库检索
    if has_knowledge_result(knowledge_reply):
        logger.info("route to knowledge skill by implicit match")
        return reply_with_text(knowledge_reply, stream_print)

    logger.info("route to llm")#不调用工具直接使用大模型时
    return call_llm_with_model(
        messages,
        model=config.model,
        stream=stream,
        stream_print=stream_print,
    )


def has_knowledge_result(text: str) -> bool:
    """判断知识库是否真的查到了内容。"""
    return text not in {NO_KNOWLEDGE_RESULT, EMPTY_KNOWLEDGE_QUERY}


def reply_with_text(text: str, stream_print: bool) -> str:
    """需要 CLI 实时打印时，直接打印本地工具结果。"""
    if stream_print:
        print(text, end="", flush=True)
    return text

def run_agent_stream(messages: list[dict[str,str]])->Iterator[str]:
    """流式agent：本地工具直接返回一段，LLM按chunk返回"""

    user_input  = messages[-1]["content"]

    tool_result = route_tool_by_rule(user_input, TOOLS)
    if tool_result is not None:
        yield tool_result.content
        return

    planned_result = run_planned_tool(user_input)
    if planned_result is not None:
        yield planned_result.content
        return

    knowledge_reply  = search_knowledge(user_input)
    if has_knowledge_result(knowledge_reply):
        logger.info("route tp knowledge skill by implicit match")
        yield knowledge_reply
        return

    logger.info("route to llm stream")
    yield from stream_llm_chunks(messages)#yield from
