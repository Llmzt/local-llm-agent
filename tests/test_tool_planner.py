"""llm工具路由测试"""
from service.tool_planner import (
    build_planner_prompt,
    normalize_user_input_for_cache,
    parse_tool_plan,
    build_cache_key,
)
from service.tool_router import ToolPlan, ToolSpec
import pytest
import service.tool_planner as planner_module

@pytest.fixture(autouse=True)#执行测试前自动清理缓存
def clear_plan_cache():
    planner_module._PLAN_CACHE.clear()

def test_parse_tool_plan_with_tool():
    plan = parse_tool_plan('{"tool": "knowledge_search", "input": "FastAPI"}')

    assert plan == ToolPlan(tool="knowledge_search", input="FastAPI")


def test_parse_tool_plan_without_tool():
    plan = parse_tool_plan('{"tool": null, "input": null}')

    assert plan == ToolPlan(tool=None, input=None)


def test_parse_tool_plan_rejects_invalid_json():
    plan = parse_tool_plan("不是 JSON")

    assert plan == ToolPlan(tool=None, input=None)


def test_parse_tool_plan_rejects_invalid_field_type():
    plan = parse_tool_plan('{"tool": 123, "input": "FastAPI"}')

    assert plan == ToolPlan(tool=None, input=None)


def test_build_planner_prompt_includes_tools():
    tools = [
        ToolSpec(
            name="time",
            description="回答当前时间。",
            input_schema="时间问题",
            match=lambda text: False,
            handler=lambda text: "ok",
        )
    ]

    prompt = build_planner_prompt(tools)

    assert "time" in prompt
    assert "回答当前时间" in prompt
    assert "时间问题" in prompt


def test_build_cache_key_includes_tool_names_and_input():
    """cache_key测试"""
    tools = [
        ToolSpec(
            name="time",
            description="时间工具",
            input_schema="时间问题",
            match=lambda text: False,
            handler=lambda text: "ok",
        )
    ]

    key = build_cache_key("今天星期几", tools)

    assert "time" in key
    assert "今天星期几" in key


def test_normalize_user_input_for_cache_ignores_formatting():
    assert normalize_user_input_for_cache("现在几点？") == "现在几点"
    assert normalize_user_input_for_cache("  现在　几点! ") == "现在几点"
    assert normalize_user_input_for_cache("ＦａｓｔＡＰＩ？") == "fastapi"

import service.tool_planner as planner_module
from service.tool_router import ToolPlan, ToolSpec


def test_plan_tool_with_llm_uses_cache(monkeypatch):
    """planner缓存调用测试"""
    planner_module._PLAN_CACHE.clear()

    call_count = {"value": 0}

    def fake_call_planner_llm(messages):
        call_count["value"] += 1
        return '{"tool": "time", "input": "今天几点"}'

    monkeypatch.setattr(
        planner_module,
        "call_planner_llm",
        fake_call_planner_llm,
    )

    tools = [
        ToolSpec(
            name="time",
            description="时间工具",
            input_schema="时间问题",
            match=lambda text: False,
            handler=lambda text: "ok",
        )
    ]

    first = planner_module.plan_tool_with_llm("今天几点", tools)
    second = planner_module.plan_tool_with_llm("今天几点？", tools)

    assert first == ToolPlan(tool="time", input="今天几点")
    assert second == ToolPlan(tool="time", input="今天几点")
    assert call_count["value"] == 1
