import pytest

from service.errors import ToolError
from service.tool_router import (
    ToolPlan,
    ToolResult,
    ToolSpec,
    execute_tool,
    execute_tool_plan,
    find_tool,
    route_tool_by_rule,
)


def test_route_tool_by_rule_returns_tool_result_when_matched():
    tools = [
        ToolSpec(
            name="hello",
            description="测试工具",
            arguments_schema={"type": "object"},
            match=lambda text: "你好" in text,
            parse_rule_input=lambda text: {"name": text},
            handler=lambda args: ToolResult(content=f"命中 {args['name']}"),
        )
    ]

    result = route_tool_by_rule("你好", tools)

    assert result == ToolResult(content="命中 你好")


def test_route_tool_by_rule_returns_none_when_no_tool_matched():
    tools = [
        ToolSpec(
            name="hello",
            description="测试工具",
            arguments_schema={"type": "object"},
            match=lambda text: "你好" in text,
            parse_rule_input=lambda text: {"name": text},
            handler=lambda args: ToolResult(content="命中 hello"),
        )
    ]

    assert route_tool_by_rule("再见", tools) is None


def test_find_tool():
    tool = ToolSpec(
        name="hello",
        description="测试工具",
        arguments_schema={"type": "object"},
        match=lambda text: False,
        parse_rule_input=lambda text: {},
        handler=lambda args: ToolResult(content="ok"),
    )

    assert find_tool([tool], "hello") == tool
    assert find_tool([tool], "missing") is None


def test_execute_tool_plan_runs_known_tool():
    tools = [
        ToolSpec(
            name="hello",
            description="测试工具",
            arguments_schema={"type": "object"},
            match=lambda text: False,
            parse_rule_input=lambda text: {},
            handler=lambda args: ToolResult(content=f"hello {args['name']}"),
        )
    ]

    result = execute_tool_plan(
        ToolPlan(tool="hello", arguments={"name": "world"}),
        tools,
    )

    assert result == ToolResult(content="hello world")


def test_execute_tool_plan_returns_none_for_unknown_tool():
    result = execute_tool_plan(
        ToolPlan(tool="missing", arguments={"name": "world"}),
        [],
    )

    assert result is None


def test_execute_tool_plan_blocks_disabled_side_effect_tool():
    tools = [
        ToolSpec(
            name="write",
            description="写入工具",
            arguments_schema={"type": "object"},
            match=lambda text: False,
            parse_rule_input=lambda text: {},
            handler=lambda args: ToolResult(content="written"),
            side_effect=True,
            planner_enabled=False,
        )
    ]

    result = execute_tool_plan(
        ToolPlan(tool="write", arguments={}),
        tools,
    )

    assert result is None


def test_execute_tool_wraps_unexpected_error():
    tool = ToolSpec(
        name="bad",
        description="坏工具",
        arguments_schema={"type": "object"},
        match=lambda text: True,
        parse_rule_input=lambda text: {},
        handler=lambda args: 1 / 0,
    )

    with pytest.raises(ToolError):
        execute_tool(tool, {})