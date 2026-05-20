"""项目统一异常类型。"""


class AppError(Exception):
    """业务可预期异常基类。"""

    user_message = "程序运行出错，请稍后再试。"

    def __init__(self, message: str, user_message: str | None = None):
        super().__init__(message)
        if user_message is not None:
            self.user_message = user_message


class LLMError(AppError):
    """模型调用相关异常。"""

    user_message = "模型调用失败，请稍后重试。"


class KnowledgeError(AppError):
    """知识库相关异常。"""

    user_message = "知识库操作失败，请稍后重试。"


class ConfigError(AppError):
    """配置相关异常。"""

    user_message = "配置缺失或配置错误，请检查 .env 文件。"