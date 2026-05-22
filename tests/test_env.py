"""测试 .env 单行解析。"""
from service.core.env import _parse_env_line

def test_parse_env_line_with_plain_value():
    assert _parse_env_line("MODEL=qvq-max") == ("MODEL", "qvq-max")

def test_parse_env_line_with_quoted_value():
    assert _parse_env_line('API_KEY="abc123"') == ("API_KEY", "abc123")


def test_parse_env_line_ignores_comment_and_empty_line():
    assert _parse_env_line("# comment") is None
    assert _parse_env_line("") is None


def test_parse_env_line_rejects_invalid_line():
    assert _parse_env_line("NO_EQUAL_SIGN") is None