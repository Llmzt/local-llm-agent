"""web API入口"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent import (
    add_assistant_message,
    add_user_message,
    create_history,
    run_agent,
    trim_history,
)
from service.errors import AppError
from service.logger import get_logger
from service.session_store import SessionStore

logger = get_logger(__name__)

app = FastAPI(title="Local Agent API")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    history: list[dict[str, str]]


@app.get("/health") #客户端get + health两个动作时，执行health
def health() ->dict[str,str]:
    """健康检查接口"""
    return {"status": "ok"}

@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest) -> ChatResponse:
    """聊天接口：按 session_id 读取、更新并保存多轮历史。"""
    store = SessionStore()
    session_id = store.ensure_session(request.session_id)

    messages = create_history() + store.get_history(session_id)
    messages = trim_history(messages)

    user_input = request.message.strip()
    add_user_message(messages, user_input)
    store.append_message(session_id,"user",user_input)

    try:
        reply = run_agent(messages,stream=True,stream_print=True)
    except AppError as exc:
        logger.exception("handled application error in api")
        reply = exc.user_message
    except Exception:
        logger.exception("unexpected error in api")
        reply = "程序发生未知错误，请查看日志。"

    add_assistant_message(messages, reply)
    store.append_message(session_id,"assistant",reply)

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        history=messages,
    )
