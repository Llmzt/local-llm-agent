# chat_agent

一个面向 Agent 工程化学习与实践的本地中文智能助手。项目包含后端 API、SSE 流式输出、SQLite 持久化、结构化工具系统、LLM 工具决策，以及玻璃拟态 Web 前端。

## Highlights

- **Agent orchestration**：规则工具路由、LLM Planner、知识库兜底、普通模型回复。
- **ToolSpec 2.0**：结构化工具参数、统一 `ToolResult`、副作用工具保护。
- **Streaming UX**：基于 SSE 的真流式回复，前端边接收边渲染。
- **Session persistence**：SQLite 保存会话历史，支持历史会话列表、切换和删除。
- **Observable API**：统一异常响应、`request_id`、请求耗时日志。
- **Modern frontend**：Vite + Vanilla JavaScript，玻璃拟态 UI，Markdown 渲染和 Toast 提示。
- **Test coverage**：覆盖 Agent、工具系统、数据层、API、SSE、异常处理和 middleware。

## Architecture

```text
User
  -> Frontend / CLI / API
  -> Agent
  -> Rule Tool Router
  -> LLM Tool Planner
  -> Knowledge fallback
  -> Main LLM
  -> Response / SSE stream
```

工具调用使用结构化 JSON：

```json
{
  "tool": "knowledge_search",
  "arguments": {
    "query": "FastAPI"
  }
}
```

工具返回统一为：

```python
ToolResult(
    content="展示给用户的文本",
    metadata={"tool": "knowledge_search"},
)
```

带副作用的工具，例如 `knowledge_write`，默认不允许由 LLM Planner 自动调用，只能通过明确规则触发。

## Features

### Backend

- FastAPI Web API
- OpenAI-compatible Chat Completions
- SSE streaming endpoint
- SQLite knowledge store
- SQLite session/history store
- Unified error handling
- Request middleware with `X-Request-ID`
- Tool planner model and main response model separation

### Frontend

- Glassmorphism UI
- Streaming assistant replies
- Toast notifications
- Markdown rendering
- Thinking animation
- Session list
- Session switch/delete
- Refresh-safe history restore
- Enter to send, Shift + Enter for newline

## Tech Stack

| Layer | Tech |
| --- | --- |
| Backend | Python, FastAPI, SQLite |
| LLM | OpenAI-compatible API |
| Frontend | Vite, Vanilla JavaScript |
| UI helpers | marked, DOMPurify |
| Testing | pytest |

## Project Structure

```text
.
├── agent.py                  # Agent orchestration
├── cli.py                    # CLI entrypoint
├── service/
│   ├── api.py                # FastAPI app and routes
│   ├── config.py             # Runtime config
│   ├── env.py                # .env loader
│   ├── errors.py             # AppError hierarchy
│   ├── error_response.py     # API error payloads
│   ├── knowledge_store.py    # SQLite knowledge store
│   ├── llm.py                # LLM client wrappers
│   ├── logger.py             # Logging setup
│   ├── middleware.py         # request_id and duration logging
│   ├── request_context.py    # request context storage
│   ├── session_store.py      # Session/history store
│   ├── sqlite_store.py       # SQLite base store
│   ├── tool_adapters.py      # Tool argument adapters
│   ├── tool_planner.py       # LLM tool planner
│   └── tool_router.py        # ToolSpec and routing
├── skill/
│   ├── knowledge.py          # Knowledge search skill
│   ├── knowledge_write.py    # Knowledge write skill
│   └── time.py               # Time skill
├── frontend/                 # Vite frontend
├── tests/                    # pytest suite
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── .env.example
```

Runtime-generated local files:

```text
database/
logs/
```

## Quick Start

Create a virtual environment:

```bash
python -m venv venv
```

Install backend dependencies:

```bash
venv/bin/pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Create local config:

```bash
cp .env.example .env
```

Set at least:

```bash
API_KEY="your api key"
```

Example config:

```bash
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL="qvq-max-2025-03-25"
PLANNER_MODEL="qwen-turbo"
REQUEST_TIMEOUT="30"
MAX_RETRIES="2"
LOG_LEVEL="INFO"
LOG_FILE="./logs/agent.log"
```

## Run

### CLI

```bash
venv/bin/python cli.py
```

Exit commands:

```text
exit
quit
q
```

### API

```bash
venv/bin/uvicorn service.api:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Chat:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"现在几点？"}'
```

SSE streaming chat:

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"讲一个短故事"}'
```

### Frontend

Start backend first:

```bash
venv/bin/uvicorn service.api:app --host 127.0.0.1 --port 8000
```

Start frontend:

```bash
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## API Overview

### Session

Continue with a session:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"继续","session_id":"your_session_id"}'
```

Get session history:

```bash
curl http://127.0.0.1:8000/sessions/{session_id}
```

List recent sessions:

```bash
curl http://127.0.0.1:8000/sessions
```

Delete a session:

```bash
curl -X DELETE http://127.0.0.1:8000/sessions/{session_id}
```

### Error Shape

JSON API errors use a stable shape:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "LLM_ERROR",
    "message": "模型调用失败，请稍后重试。",
    "request_id": "..."
  }
}
```

SSE errors are sent as:

```text
event: error
data: {"code":"LLM_ERROR","message":"模型调用失败，请稍后重试。","request_id":"..."}
```

## Knowledge Base

Search:

```text
查询知识库 Python
搜索 FastAPI
```

Write:

```text
添加知识：标题 | 内容 | 关键词
```

Example:

```text
添加知识：FastAPI | FastAPI 是一个 Python Web API 框架。 | Python,API
```

Storage:

```text
database/knowledge.db
database/sessions.db
```

## Tests

Install test dependencies:

```bash
venv/bin/pip install -r requirements-dev.txt
```

Run all tests:

```bash
venv/bin/python -m pytest -q
```

Current coverage includes:

- environment parsing
- Agent flow
- ToolSpec routing
- LLM planner parsing and cache
- SQLite stores
- session/history
- API and SSE endpoints
- error responses
- request middleware

Tests use temporary databases and do not modify local runtime data.

## Local Artifacts

Do not commit:

```text
.env
venv/
logs/
database/*.db
frontend/node_modules/
frontend/dist/
```

## Roadmap

- Docker deployment
- database migration mechanism
- RAG / vector search
- prompt template management
- user authentication and permissions
- richer frontend interactions

## License

MIT
