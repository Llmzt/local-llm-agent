"""测试大模型对话与回复"""
import agent
from service.tools.tool_router import ToolResult


def test_create_history_contains_system_prompt():
    history = agent.create_history()

    assert history[0]["role"] == "system"
    assert "content" in history[0]


def test_trim_history_keeps_system_message_and_recent_rounds():
    messages = agent.create_history()

    for i in range(20):
        messages.append({"role": "user", "content": f"user {i}"})
        messages.append({"role": "assistant", "content": f"assistant {i}"})

    trimmed = agent.trim_history(messages, max_rounds=3)

    assert trimmed[0]["role"] == "system"
    assert len(trimmed) == 1 + 3 * 2
    assert trimmed[-1]["content"] == "assistant 19"


def test_run_agent_uses_planner_for_time_tool(monkeypatch):
    messages = agent.create_history()
    agent.add_user_message(messages, "今天日期？")

    monkeypatch.setattr(
        agent,
        "run_planned_tool",
        lambda text: ToolResult(content="2026-05-22 13:16:40"),
    )

    reply = agent.run_agent(messages, stream=False)

    assert len(reply) == 19
    assert reply[4] == "-"
    assert reply[7] == "-"
    assert reply[13] == ":"

def test_run_agent_uses_planned_tool(monkeypatch):
    """大模型决策工具调用测试"""

    monkeypatch.setattr(agent, "search_knowledge", lambda text: "没有找到相关知识。")
    monkeypatch.setattr(
    agent,
    "run_planned_tool",
    lambda text: ToolResult(content="规划工具回复"),
)
    messages = agent.create_history()
    agent.add_user_message(messages, "帮我找一下 FastAPI")

    reply = agent.run_agent(messages, stream=False)

    assert reply == "规划工具回复"

def test_run_agent_uses_knowledge_when_found(monkeypatch):
    """隐式知识库检索调用测试"""
    def fake_search_knowledge(user_input):
        return "- FastAPI：测试内容"
    monkeypatch.setattr(agent, "run_planned_tool", lambda text: None)
    monkeypatch.setattr(agent, "search_knowledge", fake_search_knowledge)

    messages = agent.create_history()
    agent.add_user_message(messages, "FastAPI")

    reply = agent.run_agent(messages, stream=False)

    assert reply == "- FastAPI：测试内容"


def test_run_agent_falls_back_to_llm_when_no_knowledge(monkeypatch):
    """不调用工具不调用隐式知识库检索，直接测试大模型回复"""
    monkeypatch.setattr(agent, "run_planned_tool", lambda text: None)
    monkeypatch.setattr(agent, "search_knowledge", lambda text: "没有找到相关知识。")
    monkeypatch.setattr(
        agent,
        "call_llm_with_model",
        lambda messages, model, stream=True, stream_print=False: "LLM 回复",
    )

    messages = agent.create_history()
    agent.add_user_message(messages, "讲个笑话")

    reply = agent.run_agent(messages, stream=False)

    assert reply == "LLM 回复"
