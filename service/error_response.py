"""将异常转换为稳定的API错误结构"""

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from service.errors import AppError
from service.request_context import get_request_id



def error_payload(code: str, message: str) -> dict:
    """统一错误 payload"""
    return {
        "ok":False,
        "data": None,
        "error":{
            "code": code,
            "message": message,
            "request_id":get_request_id(),
        },
    }

#请求格式有问题，尚未调用接口
def validation_error_payload(exc: RequestValidationError)->dict:
    """请求校验异常payload"""
    return error_payload(code="INVALID_REQUEST",message="请求参数不合法")

#请求内容不存在
def http_error_payload(exc: HTTPException) ->dict:
    """HTTPException payload"""
    message = str(exc.detail) if exc.detail else "请求失败"
    return error_payload(code="HTTP_ERROR",message=message)

#可预期业务错误
def app_error_payload(exc:AppError) ->dict:
    """业务异常payload"""
    return error_payload(code=exc.code,message=exc.user_message)

#兜底
def unexpected_error_payload()->dict:#无需exc形参，因为Python异常细节需要隔离
    """未知异常payload"""
    return error_payload(code="INETERNAL_ERROR",message="程序发生未知错误，请查看日志")