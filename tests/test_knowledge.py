"""测试知识库查询词清洗、写入格式解析。"""
from skill.knowledge import extract_query
from skill.knowledge_write import parse_knowledge_text, remove_add_prefix


def test_extract_query_removes_common_words():
    assert extract_query("查询知识库 FastAPI") == "FastAPI"


def test_extract_query_strips_punctuation():
    assert extract_query("什么是 Python？") == "Python"


def test_remove_add_prefix():
    assert remove_add_prefix("添加知识：标题 | 内容 | 关键词") == "标题 | 内容 | 关键词"


def test_parse_knowledge_text_with_keywords():
    assert parse_knowledge_text("标题 | 内容 | 关键词") == ("标题", "内容", "关键词")


def test_parse_knowledge_text_without_keywords():
    assert parse_knowledge_text("标题 | 内容") == ("标题", "内容", "")


def test_parse_knowledge_text_rejects_invalid_input():
    assert parse_knowledge_text("只有标题") is None
    assert parse_knowledge_text(" | 内容") is None
    assert parse_knowledge_text("标题 | ") is None