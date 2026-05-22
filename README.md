# chat_agent

一个本地中文智能 Agent 聊天助手。项目包含后端 API、SSE 流式输出、SQLite 持久化、结构化工具系统、LLM 工具决策、统一异常处理、请求追踪，以及玻璃拟态 Web 前端。

## 项目亮点

- **Agent 编排**：规则工具路由、LLM Planner、知识库兜底、普通模型回复。
- **ToolSpec 2.0**：结构化工具参数、统一 `ToolResult`、副作用工具保护。
- **流式体验**：基于 SSE 的真流式回复，前端边接收边渲染。
- **会话持久化**：SQLite 保存会话历史，支持历史会话列表、切换和删除。
- **可观测 API**：统一异常响应、`request_id`、请求耗时日志。
- **现代前端**：Vite + Vanilla JavaScript，玻璃拟态 UI，Markdown 渲染和 Toast 提示。
- **Docker 部署**：提供前后端 Dockerfile 和 Docker Compose 本地部署配置。
- **测试覆盖**：覆盖 Agent、工具系统、数据层、API、SSE、异常处理和 middleware。

## 架构概览

```text
用户
  -> 前端 / CLI / API
  -> Agent
  -> 规则工具路由
  -> LLM 工具决策
  -> 知识库兜底
  -> 主回复模型
  -> 响应 / SSE 流
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

## 功能

### 后端

- FastAPI Web API
- OpenAI 兼容的 Chat Completions 调用
- SSE 流式输出接口
- SQLite 知识库存储
- SQLite 会话和历史消息存储
- 统一异常处理
- 带 `X-Request-ID` 的请求中间件
- 工具决策模型与主回复模型分离

### 前端

- 玻璃拟态 UI
- 助手回复流式渲染
- Toast 提示
- Markdown 渲染
- 思考动画
- 历史会话列表
- 会话切换和删除
- 刷新后自动恢复历史对话
- 回车发送，Shift + Enter 换行

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | Python, FastAPI, SQLite |
| LLM | OpenAI-compatible API |
| 前端 | Vite, Vanilla JavaScript |
| UI 辅助 | marked, DOMPurify |
| 测试 | pytest |

## 项目结构

```text
.
├── agent.py                  # Agent 编排主流程
├── cli.py                    # 命令行入口
├── service/
│   ├── llm.py                # LLM 客户端封装
│   ├── api/
│   │   ├── api.py            # FastAPI 应用和路由
│   │   └── error_response.py # API 错误响应结构
│   ├── core/
│   │   ├── config.py         # 运行时配置
│   │   ├── env.py            # .env 与项目根目录路径
│   │   ├── errors.py         # 统一异常类型
│   │   ├── logger.py         # 日志初始化
│   │   ├── middleware.py     # request_id 和耗时日志
│   │   └── request_context.py
│   ├── stores/
│   │   ├── knowledge_store.py
│   │   ├── session_store.py
│   │   └── sqlite_store.py
│   └── tools/
│       ├── tool_adapters.py
│       ├── tool_planner.py
│       └── tool_router.py
├── skill/
│   ├── knowledge.py          # 知识库查询能力
│   ├── knowledge_write.py    # 知识库写入能力
│   └── time.py               # 时间能力
├── frontend/                 # Vite 前端
├── tests/                    # pytest 测试
├── Dockerfile.backend        # 后端生产镜像
├── docker-compose.yml        # 本地全栈部署
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── .env.example
```

运行时生成的本地文件：

```text
database/
logs/
```

## 快速开始

创建虚拟环境：

```bash
python -m venv venv
```

安装后端依赖：

```bash
venv/bin/pip install -r requirements.txt
```

安装前端依赖：

```bash
cd frontend
npm install
```

创建本地配置：

```bash
cp .env.example .env
```

至少需要设置：

```bash
API_KEY="your api key"
```

配置示例：

```bash
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL="qvq-max-2025-03-25"
PLANNER_MODEL="qwen-turbo"
REQUEST_TIMEOUT="30"
MAX_RETRIES="2"
LOG_LEVEL="INFO"
LOG_FILE="./logs/agent.log"
```

## 运行

### 命令行

```bash
venv/bin/python cli.py
```

退出命令：

```text
exit
quit
q
```

### API

```bash
venv/bin/uvicorn service.api.api:app --host 127.0.0.1 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

普通聊天：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"现在几点？"}'
```

SSE 流式聊天：

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"讲一个短故事"}'
```

### 前端

先启动后端：

```bash
venv/bin/uvicorn service.api.api:app --host 127.0.0.1 --port 8000
```

再启动前端：

```bash
cd frontend
npm run dev
```

打开：

```text
http://127.0.0.1:5173
```

## Docker 部署

构建并启动完整服务：

```bash
docker compose up -d --build
```

打开前端：

```text
http://127.0.0.1:5173
```

检查后端：

```bash
curl http://127.0.0.1:8000/health
```

停止服务：

```bash
docker compose down
```

Docker Compose 会挂载本地运行数据：

```text
./database -> /app/database
./logs     -> /app/logs
```

运行 Docker 前，请确认 `.env` 已存在，并且包含有效的模型配置。

本地 Docker 模式下，前端当前调用：

```text
http://127.0.0.1:8000
```

如果部署到远程服务器或域名，需要同步调整前端 API 地址和后端 CORS 白名单。

## API 概览

### 会话

携带 `session_id` 继续对话：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"继续","session_id":"your_session_id"}'
```

获取会话历史：

```bash
curl http://127.0.0.1:8000/sessions/{session_id}
```

列出最近会话：

```bash
curl http://127.0.0.1:8000/sessions
```

删除会话：

```bash
curl -X DELETE http://127.0.0.1:8000/sessions/{session_id}
```

### 错误响应结构

JSON API 错误使用稳定结构：

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

SSE 错误会以事件形式发送：

```text
event: error
data: {"code":"LLM_ERROR","message":"模型调用失败，请稍后重试。","request_id":"..."}
```

## 知识库

查询：

```text
查询知识库 Python
搜索 FastAPI
```

写入：

```text
添加知识：标题 | 内容 | 关键词
```

示例：

```text
添加知识：FastAPI | FastAPI 是一个 Python Web API 框架。 | Python,API
```

存储位置：

```text
database/knowledge.db
database/sessions.db
```

## 测试

安装测试依赖：

```bash
venv/bin/pip install -r requirements-dev.txt
```

运行全部测试：

```bash
venv/bin/python -m pytest -q
```

当前覆盖内容：

- 环境变量解析
- Agent 主流程
- ToolSpec 路由
- LLM Planner 解析和缓存
- SQLite 数据存储
- 会话和历史消息
- API 与 SSE 接口
- 错误响应
- 请求中间件

测试使用临时数据库，不会修改本地运行数据。

## 本地文件

不要提交：

```text
.env
venv/
logs/
database/*.db
frontend/node_modules/
frontend/dist/
```

## 后续规划

- 数据库迁移机制
- 可配置的前端 API 地址
- 可配置的 CORS 白名单
- 模块边界稳定后的进一步包拆分
- RAG / vector search
- Prompt 模板管理
- 用户系统与权限
- 更丰富的前端交互

## 许可证

MIT
