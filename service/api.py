"""web API入口"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request,Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse,StreamingResponse
from pydantic import BaseModel, Field
import json
from collections.abc import Iterator

from agent import (
    add_assistant_message,
    add_user_message,
    create_history,
    run_agent,
    trim_history,
    run_agent_stream,
)
from service.error_response import (
    app_error_payload,
    error_payload,
    http_error_payload,
    unexpected_error_payload,
    validation_error_payload,
)
from service.logger import get_logger
from service.session_store import SessionStore
from service.middleware import request_context_middleware
from service.errors import AppError, RequestError

logger = get_logger(__name__)

app = FastAPI(title="Local Agent API") 

app.middleware("http")(request_context_middleware)  #装饰器的手动写法；中间件注册器（HTTP请求的处理中间件）
                                                    #每当HTTP请求到来，先交给中间件，中间件交给request_context_middleware

app.add_middleware(#前后端连接的关键
    CORSMiddleware,#中间件跨域
    allow_origins=[#访问后端的前端白名单
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials = True,#允许携带cookie等身份信息
    allow_methods = ["*"],#允许全部请求方法
    allow_headers = ["*"],#允许全部请求头
)

#-----------------------------工具函数---------------------------------- 

#依赖隔离,状态与行为分离
def get_session_store() -> SessionStore:
    """创建session_store;后续可以用于测试时monkeypatch进行临时替代函数"""
    return SessionStore()

def sse_event(event: str,data: dict) ->str:
    """把事件转换成SSE文本格式"""
    return f"event: {event}\ndata: {json.dumps(data,ensure_ascii=False)}\n\n"   #注意键值对空格格式

def stream_chat_events(request: ChatStreamRequest) ->Iterator[str]:
    """流式聊天事件生成器"""
    user_input = request.message.strip()
    if not user_input:
        exc = RequestError(
            "empty chat message",
            user_message="message 不能为空",
            code="EMPTY_MESSAGE",
            status_code=422,
        )
        yield sse_event(
            "error",
            app_error_payload(exc)["error"] #sse无需说明类型属性（event已具备），而json需要
        )
        return
    store = get_session_store()
    session_id = store.ensure_session(request.session_id)
    messages = create_history()+store.get_history(session_id)
    messages = trim_history(messages)

    add_user_message(messages, user_input)
    store.append_message(session_id,"user",user_input)

    yield sse_event(
        "session",
        {
            "session_id":session_id,
        },
    )

    full_reply = ""

    try:
        for chunk in run_agent_stream(messages):
            full_reply+=chunk
            yield sse_event(
                "chunk",
                {"content":chunk,
                },
            )
        add_assistant_message(messages,full_reply)
        store.append_message(session_id,"assistant",full_reply)

        yield sse_event(
            "done",
            {
                "reply":full_reply,
                "session_id":session_id,
                "history":messages,
            },
        )
    except AppError as exc:
        logger.exception("handled stream application error in api")
        yield sse_event(
            "error",
            app_error_payload(exc)["error"]
        )
    except Exception:
        logger.exception("unexpected stream error in api")
        yield sse_event(
            "error",
            unexpected_error_payload()["error"]
        )

#---------------统一api返回格式-----------------
class ErrorInfo(BaseModel):
    code:str
    message:str

class HealthData(BaseModel):
    status:str

class HealthResponse(BaseModel):
    ok: bool
    data: HealthData
    error: ErrorInfo | None = None

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    """pydantic 用户输入参数校验转换"""
    message: str = Field(min_length=1,max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)#限制session_id字段长度，防止恶意输入占用数据库、进行dos攻击等

class SessionData(BaseModel):
    session_id: str
    history: list[MessageItem]

class SessionResponse(BaseModel):
    ok:bool
    data: SessionData
    error: ErrorInfo | None = None

#规范化响应结构，数据与状态分离
class ChatData(BaseModel):
    reply: str
    session_id:str
    history: list[MessageItem]

class ChatResponse(BaseModel):
    ok: bool
    data: ChatData
    error: ErrorInfo | None = None

class SessionSummaryItem(BaseModel):
    session_id:str
    title: str
    created_at:str
    updated_at:str
    message_count: int

class SessionListData(BaseModel):
    sessions:list[SessionSummaryItem]

class SessionListResponse(BaseModel):
    ok:bool
    data:SessionListData
    error:ErrorInfo| None = None

class DeleteSessionData(BaseModel):
    deleted: bool
    session_id: str

class DeleteSessionResponse(BaseModel):
    ok:bool
    data:DeleteSessionData
    error: ErrorInfo | None = None

class ChatStreamRequest(BaseModel):
    """流式输出模型"""
    message: str = Field(min_length=1,max_length=4000)
    session_id: str | None = Field(default=None,max_length=128)



#----------------------异常响应接口----------------------

"""捕获所有可能的异常，进行处理并统一日志入口（业务价值不高的错误只raise错误，无需第一时间写日志）"""
def build_error_response(status_code:int,payload:dict)->JSONResponse:
    """统一错误响应格式"""
    return JSONResponse(status_code=status_code,
                        content=payload
                        )

@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request,exc: RequestValidationError)->JSONResponse:
    """请求参数不合法响应"""
    logger.info("request validation failed: %s",exc)
    return build_error_response(status_code=422, payload=validation_error_payload(exc))

@app.exception_handler(HTTPException)
async def handle_http_error(request: Request, exc: HTTPException,)->JSONResponse:
    """主动抛出的 HTTP 错误。"""
    #通常为请求资源不存在等，为主动抛出，不需要记日志
    return build_error_response(status_code=exc.status_code, payload=http_error_payload(exc))

@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError,)->JSONResponse:
    """业务内可预期错误"""
    logger.exception("handled application error in api")
    
    return build_error_response(status_code=exc.status_code,payload=app_error_payload(exc))

@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request,exc: Exception,)->JSONResponse:
    """兜底，避免把Python异常细节暴露给客户端"""
    logger.exception("unexpected error in api")
    return build_error_response(status_code=500,payload=unexpected_error_payload())#不传exc，防止暴露异常细节


#-----------------------正常响应接口-----------------------
@app.get("/health",response_model=HealthResponse) #客户端get + health两个动作时，执行health响应
def health() ->HealthResponse:
    """健康检查接口"""
    return HealthResponse(
        ok=True,
        data=HealthData(status="ok"),
        error=None,
    )

@app.get("/sessions/{session_id}",response_model=SessionResponse,)
def get_session_history(session_id:str = Path(min_length=1,max_length=128))->SessionResponse:
    """读取指定session的历史消息"""
    store = get_session_store()

    if not store.session_exists(session_id):
        raise HTTPException(status_code=404,detail="session 不存在")
    
    history  = store.get_history(session_id)

    return SessionResponse(
        ok = True,
        data=SessionData(
            session_id = session_id,
            history=history,
        ),
        error=None,
    )

@app.post("/chat",response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """聊天接口：按 session_id 读取、更新并保存多轮历史。"""
    user_input = request.message.strip()
    if not user_input:
        raise RequestError(
            "empty chat message",
            user_message="message 不能为空",
            code="EMPTY_MESSAGE",
            status_code=422,
        )
    
    store = get_session_store()
    session_id = store.ensure_session(request.session_id)

    messages = create_history() + store.get_history(session_id)
    messages = trim_history(messages)

    add_user_message(messages, user_input)
    store.append_message(session_id,"user",user_input)

    reply = run_agent(messages,stream=True,stream_print=False,)

    add_assistant_message(messages,reply)
    store.append_message(session_id,"assistant",reply)

    return ChatResponse(
        ok=True,
        data=ChatData(reply=reply,session_id=session_id,history=messages,),
        error=None,
    )

@app.get("/sessions",response_model=SessionListResponse)
def list_sessions() ->SessionListResponse:
    """列出最近对话"""
    store = get_session_store()
    sessions = store.list_sessions()

    return SessionListResponse(ok=True,data=SessionListData(sessions=sessions),error=None)

@app.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
def delete_session(
    session_id: str = Path(min_length=1, max_length=128),
) -> DeleteSessionResponse:
    """删除指定 session。"""
    store = get_session_store()
    deleted = store.delete_session(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="session 不存在")

    return DeleteSessionResponse(
        ok=True,
        data=DeleteSessionData(
            deleted=True,
            session_id=session_id,
        ),
        error=None,
    )

@app.post("/chat/stream") #流式输出响应
def chat_stream(request:ChatStreamRequest)->StreamingResponse:
    """SSE 流式聊天接口"""
    return StreamingResponse(
        stream_chat_events(request),
        media_type="text/event-stream",#HTTP文本类型
        headers={                       #HTTP响应头
            "Cache-Control":"no-cache",#不要缓存，返回实时流
            "X-Accel-Buffering":"no",   #立刻返回，不要缓冲
        },
    )
