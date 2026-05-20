"""模型调用：封装 CLI Agent 需要的聊天补全。"""

import time

from service.config import load_config
from service.logger import get_logger

from service.errors import LLMError

logger = get_logger(__name__)

_client = None
_config = None


def get_config():
    """读取并缓存配置。"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_client():
    """创建并缓存 OpenAI-compatible 客户端。"""
    global _client
    if _client is not None:
        return _client

    from openai import OpenAI

    config = get_config()
    _client = OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.request_timeout,
        max_retries=0,
    )
    return _client


def call_llm(
    messages: list[dict[str, str]],
    stream: bool = True,
    stream_print: bool = False,
) -> str:
    """调用模型并返回完整文本。"""
    config = get_config()
    request = {
        "model": config.model,
        "messages": messages,
        "stream": stream,
    }

    logger.info("calling llm: model=%s stream=%s", config.model, stream)

    if stream:
        return call_llm_stream(request, stream_print)
    return call_llm_once(request)


def call_llm_once(request: dict) -> str:
    """非流式调用，适合调试。"""
    response = request_with_retry(
        lambda: get_client().chat.completions.create(**request)
    )
    if not response.choices:
        raise LLMError("llm returned no choices", user_message="模型没有返回结果。")

    reply = response.choices[0].message.content
    if not reply:
        raise LLMError("llm returned empty content", user_message="模型返回内容为空。")
    return reply


def call_llm_stream(request: dict, stream_print: bool) -> str:
    """流式调用，CLI 可以边生成边打印。"""
    response = request_with_retry(
        lambda: get_client().chat.completions.create(**request)
    )

    full_reply = ""
    for chunk in response:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if not delta:
            continue
        if stream_print:
            print(delta, end="", flush=True)
        full_reply += delta

    if not full_reply:
        raise LLMError("llm returned empty content", user_message="模型返回内容为空。")
    return full_reply


def request_with_retry(create_request):
    """模型请求失败时做少量重试。"""
    config = get_config()

    for attempt in range(config.max_retries + 1):
        try:
            return create_request()
        except Exception as exc:
            logger.warning(
                "llm request failed: attempt=%s max_retries=%s error=%s",
                attempt + 1,
                config.max_retries,
                exc,
            )

            if attempt >= config.max_retries:
                logger.exception("llm request finally failed")
                raise LLMError(
                    f"llm request failed after retries: {exc}",
                    user_message="模型调用失败，请稍后重试。",
                ) from exc

            time.sleep(min(2**attempt, 4))