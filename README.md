# chat_agent

一个用于学习 Agent 工程化的极简中文智能助手。

## 项目特性

- 规则工具路由
- LLM 工具决策规划
- ToolSpec 2.0 结构化工具系统
- SQLite 知识库查询与写入
- session/history 持久化
- SSE 真流式输出
- FastAPI Web API
- Vite 原生前端
- 统一异常处理
- 自动化测试

核心流程：

```text
用户输入
  -> 规则工具路由
  -> LLM 工具规划
  -> 知识库兜底
  -> 普通 LLM 回复
```

## 工具系统

工具通过 `ToolSpec` 注册，支持结构化参数、统一结果和副作用保护。

当前工具：

- `time`：返回当前本地时间。
- `knowledge_search`：查询本地 SQLite 知识库。
- `knowledge_write`：写入本地知识库。

工具调用结果统一为 `ToolResult`：

```python
ToolResult(
    content="展示给用户的文本",
    metadata={"tool": "tool_name"},
)
```

LLM planner 输出结构化 JSON：

```json
{
  "tool": "knowledge_search",
  "arguments": {
    "query": "FastAPI"
  }
}
```

带副作用的工具，例如 `knowledge_write`，默认不允许由 planner 自动调用，只允许通过明确规则命中触发，避免误写入本地数据。

## 技术栈

后端：

- Python
- FastAPI
- SQLite
- OpenAI-compatible API
- pytest

前端：

- Vite
- Vanilla JavaScript
- marked
- DOMPurify

## 项目结构

```text
.
├── agent.py                  # Agent 主流程
├── cli.py                    # CLI 入口
├── service/
│   ├── api.py                # FastAPI API
│   ├── config.py             # 配置读取
│   ├── env.py                # .env 加载
│   ├── errors.py             # 统一异常
│   ├── error_response.py     # API 错误响应
│   ├── knowledge_store.py    # SQLite 知识库
│   ├── llm.py                # LLM 调用封装
│   ├── logger.py             # 日志系统
│   ├── session_store.py      # session/history 持久化
│   ├── sqlite_store.py       # SQLite 基础层
│   ├── tool_adapters.py      # 结构化工具适配器
│   ├── tool_planner.py       # LLM 工具规划
│   └── tool_router.py        # 工具注册与路由
├── skill/
│   ├── knowledge.py          # 知识库查询
│   ├── knowledge_write.py    # 知识库写入
│   └── time.py               # 时间工具
├── frontend/                 # 前端
├── tests/                    # pytest 测试
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── .env.example
```

运行后会自动生成：

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

安装测试依赖：

```bash
venv/bin/pip install -r requirements-dev.txt
```

安装前端依赖：

```bash
cd frontend
npm install
```

## 配置

复制配置文件：

```bash
cp .env.example .env
```

至少需要配置：

```bash
API_KEY="你的模型 API Key"
```

示例：

```bash
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL="qvq-max-2025-03-25"
PLANNER_MODEL="qwen-turbo"
REQUEST_TIMEOUT="30"
MAX_RETRIES="2"
LOG_LEVEL="INFO"
LOG_FILE="./logs/agent.log"
```

说明：

- `MODEL` 用于普通回答。
- `PLANNER_MODEL` 用于工具决策规划。
- 模型接口使用 OpenAI-compatible Chat Completions API。

## 运行 CLI

```bash
venv/bin/python cli.py
```

退出命令：

```text
exit
quit
q
```

## 运行 API

```bash
venv/bin/uvicorn service.api:app --host 127.0.0.1 --port 8000
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

## Session 管理

API 会自动返回 `session_id`。后续请求带上同一个 `session_id` 即可恢复历史上下文：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"继续","session_id":"你的session_id"}'
```

获取历史会话：

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

## 运行前端

先启动后端 API：

```bash
venv/bin/uvicorn service.api:app --host 127.0.0.1 --port 8000
```

再启动前端：

```bash
cd frontend
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173
```

前端支持：

- SSE 流式回复
- Markdown 消息渲染
- 思考动画
- 历史会话列表
- 切换和删除会话
- 页面刷新后自动恢复历史
- Enter 发送，Shift + Enter 换行

## 知识库

查询知识：

```text
查询知识库 Python
搜索 FastAPI
```

写入知识：

```text
添加知识：标题 | 内容 | 关键词
```

示例：

```text
添加知识：FastAPI | FastAPI 是一个 Python Web API 框架。 | Python,API
```

## 数据存储

知识库：

```text
database/knowledge.db
```

会话历史：

```text
database/sessions.db
```

## 测试

运行全部测试：

```bash
venv/bin/python -m pytest -q
```

当前覆盖：

- `.env` 解析
- 工具路由
- ToolSpec 结构化工具系统
- LLM Planner
- SQLite 数据层
- session/history
- FastAPI API
- SSE 流式接口
- Agent 主流程

测试使用临时数据库，不会污染真实数据。

## 本地运行产物

以下内容不应提交：

```text
.env
venv/
logs/
database/*.db
frontend/node_modules/
frontend/dist/
```

## 后续规划

可继续优化：

- Docker 部署
- request_id / 请求耗时中间件
- 数据库迁移机制
- RAG / 向量检索
- Prompt 模板系统
- 用户认证与权限
- 更完整的前端 UI

## License

MIT
