"""异常处理测试"""
from service.api.error_response import app_error_payload, error_payload
from service.core.errors import AppError, LLMError, RequestError


def test_error_payload_shape():
    payload = error_payload("TEST_ERROR", "测试错误。")

    assert payload == {
        "ok": False,
        "data": None,
        "error": {
            "code": "TEST_ERROR",
            "message": "测试错误。",
            "request_id":None,
        },
    }


def test_app_error_payload_uses_error_code_and_user_message():
    exc = AppError(
        "internal message",
        user_message="用户可见错误。",
        code="CUSTOM_ERROR",
        status_code=409,
    )

    payload = app_error_payload(exc)

    assert payload["error"]["code"] == "CUSTOM_ERROR"
    assert payload["error"]["message"] == "用户可见错误。"


def test_llm_error_defaults():
    exc = LLMError("provider failed")

    assert exc.code == "LLM_ERROR"
    assert exc.status_code == 502
    assert exc.user_message == "模型调用失败，请稍后重试。"


def test_request_error_can_override_code_and_status():
    exc = RequestError(
        "empty message",
        user_message="message 不能为空。",
        code="EMPTY_MESSAGE",
        status_code=422,
    )

    assert exc.code == "EMPTY_MESSAGE"
    assert exc.status_code == 422
    assert exc.user_message == "message 不能为空。"
