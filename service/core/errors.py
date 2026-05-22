"""项目统一异常类型。"""

#----------------------python异常对象--------------------------
class AppError(Exception):
    """业务可预期异常基类。"""
    code = "APP_ERROR"
    status_code = 400
    user_message = "程序运行出错，请稍后再试"

    def __init__(self, 
                 message: str, 
                 user_message: str | None = None,
                 code: str|None =None,status_code: 
                 int | None = None):
        super().__init__(message)
        if user_message is not None:
            self.user_message = user_message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code

class RequestError(AppError):
    """请求参数或语义错误"""
    code = "REQUEST_ERROR"
    status_code = 400   #可读性
    user_message = "请求不合法"

class ConfigError(AppError):
    """配置错误"""

    code = "CONFIG_ERROR"
    status_code = 500
    user_message = "配置缺失或错误，请检查.env文件"

class LLMError(AppError):
    """模型调用相关异常。"""

    code = "LLM_ERROR"
    status_code = 502
    user_message = "模型调用失败，请稍后重试。"


class KnowledgeError(AppError):
    """知识库相关异常。"""

    code = "KNOWLEDGE_ERROR"
    status_code = 400
    user_message = "知识库操作失败，请稍后重试。"


class SessionError(AppError):
    """会话存储异常。"""
    
    code = "SESSION_ERROR"
    status_code = 400
    user_message = "会话读写失败，请稍后再试"

class ToolError(AppError):
    """本地工具执行错误"""

    code = "TOOL_ERROR"
    status_code = 400
    user_message = "工具执行失败，请稍后再试"