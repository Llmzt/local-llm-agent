"""测试工具路由"""
import pytest

from service.errors import ToolError
from service.tool_router import (
    ToolPlan,
    ToolSpec,
    execute_tool,
    execute_tool_plan,
    find_tool,
    route_tool_by_rule,
)


def test_route_tool_by_rule_returns_handler_result_when_matched():
    tools = [
        ToolSpec(
            name="hello",
            description="测试工具",
            input_schema="任意文本",
            match=lambda text: "你好" in text,
            handler=lambda text: "命中 hello",
        )
    ]

    assert route_tool_by_rule("你好", tools) == "命中 hello"


def test_route_tool_by_rule_returns_none_when_no_tool_matched():
    tools = [
        ToolSpec(
            name="hello",
            description="测试工具",
            input_schema="任意文本",
            match=lambda text: "你好" in text,
            handler=lambda text: "命中 hello",
        )
    ]

    assert route_tool_by_rule("再见", tools) is None


def test_find_tool():
    tool = ToolSpec(
        name="hello",
        description="测试工具",
        input_schema="任意文本",
        match=lambda text: False,
        handler=lambda text: "ok",
    )

    assert find_tool([tool], "hello") == tool
    assert find_tool([tool], "missing") is None


def test_execute_tool_plan_runs_known_tool():
    tools = [
        ToolSpec(
            name="hello",
            description="测试工具",
            input_schema="任意文本",
            match=lambda text: False,
            handler=lambda text: f"hello {text}",
        )
    ]

    result = execute_tool_plan(
        ToolPlan(tool="hello", input="world"),
        tools,
    )

    assert result == "hello world"


def test_execute_tool_plan_returns_none_for_unknown_tool():
    result = execute_tool_plan(
        ToolPlan(tool="missing", input="world"),
        [],
    )

    assert result is None


def test_execute_tool_wraps_unexpected_error():
    tool = ToolSpec(
        name="bad",
        description="坏工具",
        input_schema="任意文本",
        match=lambda text: True,
        handler=lambda text: 1 / 0,
    )

    with pytest.raises(ToolError):
        execute_tool(tool, "x")