"""工具适配器测试"""

from service.tool_adapters import (
    parse_empty_arguments,
    parse_knowledge_search_arguments,
    parse_knowledge_write_arguments,
    run_time_tool,
)
from service.tool_router import ToolResult


def test_parse_empty_arguments():
    assert parse_empty_arguments("现在几点") == {}


def test_parse_knowledge_search_arguments():
    assert parse_knowledge_search_arguments("查询知识库 FastAPI") == {
        "query": "查询知识库 FastAPI",
    }


def test_parse_knowledge_write_arguments():
    assert parse_knowledge_write_arguments("添加知识：标题 | 内容 | 关键词") == {
        "text": "添加知识：标题 | 内容 | 关键词",
    }


def test_run_time_tool():
    result = run_time_tool({})

    assert isinstance(result, ToolResult)
    assert len(result.content) == 19
    assert result.metadata["tool"] == "time"