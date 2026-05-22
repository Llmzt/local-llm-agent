"""配置读取：从 .env 和环境变量里读取模型配置。"""

import os
from dataclasses import dataclass
from service.errors import ConfigError
from service.env import load_env_file


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    base_url: str
    model: str
    request_timeout: float
    max_retries: int
    planner_model: str


def load_config() -> AppConfig:
    """读取 Agent 运行所需配置。"""
    load_env_file()

    api_key = os.getenv("API_KEY", "").strip()
    if not api_key:
        raise ConfigError("missing API_KEY environment variable",)
    

    return AppConfig(
        api_key=api_key,
        #getenv(a,b):获取参数a，如果参数未定义，默认为b
        base_url=os.getenv(
            "BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
        model=os.getenv("MODEL", "qvq-max-2025-03-25"),
        request_timeout=get_float("REQUEST_TIMEOUT", 30.0),
        max_retries=get_int("MAX_RETRIES", 2),
        planner_model=os.getenv("PLANNER_MODEL", "qwen-turbo"),
    )


def get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


def get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)
