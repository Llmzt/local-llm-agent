"""测试工具路由"""

from service.tool_router import Tool, route_tool


def test_route_tool_returns_handler_result_when_matched():
    tools = [
        Tool(
            name="hello",
            description="测试tool",
            match = lambda text: "你好" in text,
            handler = lambda text: "命中 hello",
        )
    ]
    assert route_tool("你好",tools) == "命中 hello"


def test_route_tool_returns_none_when_no_tool_matched():
    tools = [
        Tool(
            name="hello",
            description="测试tool",
            match=lambda text: "你好" in text,
            handler=lambda text: "命中 hello",
        )
    ]

    assert route_tool("不好", tools) is None