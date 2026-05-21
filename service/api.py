"""web API入口"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request,Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent import (
    add_assistant_message,
    add_user_message,
    create_history,
    run_agent,
    trim_history,
)
from service.errors import AppError, ConfigError, KnowledgeError,LLMError
from service.logger import get_logger
from service.session_store import SessionStore

logger = get_logger(__name__)

app = FastAPI(title="Local Agent API")

app.add_middleware(
    CORSMiddleware,#中间件跨域
    allow_origins=[#访问后端的前端白名单
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials = True,#允许携带cookie等身份信息
    allow_methods = ["*"],#允许全部请求方法
    allow_headers = ["*"],#允许全部请求头
)

#统一api返回格式
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

#依赖隔离
def get_session_store() -> SessionStore:
    """创建session_store;后续可以用于测试时monkeypatch进行临时替代函数"""
    return SessionStore()

#-----------异常响应-------------
def build_error_response(status_code:int,code: str, message:str)->JSONResponse:
    """统一错误响应格式"""
    return JSONResponse(status_code=status_code,
                        content={
                            "ok":False,
                            "data": None,
                            "error":{
                                "code": code,
                                "message":message,
                            }
                        }
                        )

@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request,exc: RequestValidationError)->JSONResponse:
    """请求参数不合法响应"""
    logger.info("request validation failed: %s",exc)
    return build_error_response(status_code=422, code="INVALID_REQUEST",message="请求参数不合法")

@app.exception_handler(HTTPException)
async def handle_http_error(request: Request, exc: HTTPException,)->JSONResponse:
    """主动抛出的 HTTP 错误。"""
    message = str(exc.detail) if exc.detail else "请求失败。"
    return build_error_response(status_code=exc.status_code, code="HTTP_ERROR", message=message,)

@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError,)->JSONResponse:
    """业务内可预期错误"""
    logger.exception("handled application error in api")

    status_code = 400
    code = "APP_ERROR"

    if isinstance(exc, ConfigError):
        status_code = 500
        code = "CONFIG_ERROR"
    elif isinstance(exc, LLMError):
        status_code = 502
        code = "LLM_ERROR"
    elif isinstance(exc, KnowledgeError):
        status_code = 400
        code = "KNOWLEDGE_ERROR"
    
    return build_error_response(status_code= status_code,code=code,message=exc.user_message,)

@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request,exc: Exception,)->JSONResponse:
    """兜底，避免把Python异常细节暴露给客户端"""
    logger.exception("unexpected error in api")
    return build_error_response(status_code=500,code="INTERNAL_ERROR",message="程序发生未知错误，请查看日志。",)


#---------正常响应--------
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


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest) -> ChatResponse:
    """聊天接口：按 session_id 读取、更新并保存多轮历史。"""
    user_input = request.message.strip()
    if not user_input:
        raise HTTPException(status_code=422, detail="message 不能为空。")
    
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
