"""请求上下文：保存当前请求的 request_id"""

from contextvars import ContextVar

_request_id_var: ContextVar[str|None] = ContextVar(     #前加下划线：模块私有变量，不许外部操作
                                                        #用于封装
    "request_id",
    default=None
)

def set_request_id(request_id:str) ->None:
    """设置当前请求的 request_id"""
    _request_id_var.set(request_id)

def get_request_id() -> str|None:
    """获取当前请求的 request_id"""
    return _request_id_var.get()