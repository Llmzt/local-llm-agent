"""FASTAPI中间件"""

import time
import uuid
from collections.abc import Awaitable,Callable

from fastapi import Request,Response

from service.logger import get_logger
from service.request_context import set_request_id

logger = get_logger(__name__)


async def request_context_middleware(request:Request,
                                     call_next:Callable[[Request],Awaitable[Response]]  
                                     #[传参，返回]
                                    #awaitable[response]:可以返回response的可await对象（异步对象）
                                     )->Response:
    """为每个请求生成 request_id，并记录请求耗时"""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex   #X-:自定义，非标准的字段
    set_request_id(request_id)

    start_time = time.perf_counter()
    status_code = 500                   #先假设失败:防御式编程

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = (time.perf_counter()-start_time)*1000

        #response只有再call_next成功返回后才存在
        if "response" in locals():          #确定有response时(local:局部变量表)
            response.headers["X-Request-ID"]=request_id

        logger.info(
            "request finished: request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )