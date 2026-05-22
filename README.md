````markdown
# chat_agent

一个用于学习 Agent 工程化的极简中文智能助手。

- 工具路由
- LLM 工具决策
- SQLite 数据层
- session/history 持久化
- SSE 流式输出
- Web 前端
- 日志系统
- 异常处理
- 自动化测试

---

# 项目特性

## Agent 能力

- 规则工具路由
- LLM Planner 工具决策
- 本地知识库查询与写入
- 隐式知识库兜底检索
- OpenAI-compatible 模型调用

核心流程：

```text
用户输入
    ↓
规则工具路由
    ↓
LLM 工具规划
    ↓
知识库兜底
    ↓
普通 LLM 回复
````

---

## 工程化能力

* FastAPI Web API
* SSE 真流式输出
* SQLite 持久化
* 多轮 session/history
* 统一异常处理
* 日志系统
* 自动化测试
* 前后端分离

---

## 前端功能

* Web 聊天界面
* Markdown 消息渲染
* SSE 流式回复
* “思考中” 动画
* 历史会话列表
* 删除会话
* 页面刷新自动恢复历史

---

# 技术栈

## 后端

* Python
* FastAPI
* SQLite
* OpenAI-compatible API
* pytest

## 前端

* Vite
* Vanilla JavaScript
* DOMPurify
* marked

---

# 项目结构

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

运行后自动生成：

```text
database/
logs/
```

---

# 快速开始

## 1. 创建虚拟环境

```bash
python -m venv venv
```

---

## 2. 安装依赖

```bash
venv/bin/pip install -r requirements.txt
```

如需运行测试：

```bash
venv/bin/pip install -r requirements-dev.txt
```

---

## 3. 配置环境变量

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

---

# 运行方式

# CLI

```bash
venv/bin/python cli.py
```

退出命令：

```text
exit
quit
q
```

---

# 启动 API

```bash
venv/bin/uvicorn service.api:app --host 127.0.0.1 --port 8000
```

---

# API 示例

## 健康检查

```bash
curl http://127.0.0.1:8000/health
```

---

## 普通聊天

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"现在几点？"}'
```

---

## SSE 流式聊天

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"讲一个短故事"}'
```

---

# Session 持久化

API 会自动返回 `session_id`。

后续请求带上同一个 `session_id` 即可恢复历史上下文：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"继续","session_id":"你的session_id"}'
```

---

# 会话管理

## 获取历史会话

```bash
curl http://127.0.0.1:8000/sessions/{session_id}
```

---

## 列出最近会话

```bash
curl http://127.0.0.1:8000/sessions
```

---

## 删除会话

```bash
curl -X DELETE \
http://127.0.0.1:8000/sessions/{session_id}
```

---

# 前端运行

先启动后端：

```bash
venv/bin/uvicorn service.api:app --host 127.0.0.1 --port 8000
```

再启动前端：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173
```

---

# 知识库

## 查询知识

```text
查询知识库 Python
搜索 FastAPI
```

---

## 写入知识

```text
添加知识：标题 | 内容 | 关键词
```

示例：

```text
添加知识：FastAPI | FastAPI 是一个 Python Web API 框架。 | Python,API
```

---

# 数据存储

知识库：

```text
database/knowledge.db
```

会话历史：

```text
database/sessions.db
```

---

# 测试

运行全部测试：

```bash
venv/bin/python -m pytest -q
```

当前覆盖：

* `.env` 解析
* 工具路由
* LLM Planner
* SQLite 数据层
* session/history
* FastAPI API
* SSE 流式接口
* Agent 主流程

测试使用临时数据库，不会污染真实数据。

---

# 当前项目状态

当前项目已经完成：

* Agent 主流程
* Tool Router
* Tool Planner
* SQLite 数据层
* Session 持久化
* SSE 流式输出
* Web 前端
* 日志系统
* 统一异常处理
* 自动化测试


---

# 后续规划

计划继续加入：

* 更完整的 Tool Calling
* RAG / 向量检索
* 多工具协同
* Prompt 模板系统
* Tool Memory
* 长上下文管理
* 多 Agent
* Docker 部署
* 用户认证
* 更完整的前端 UI

---

# 本地运行产物

```text
.env
venv/
logs/
database/*.db
frontend/node_modules/
frontend/dist/
```

---

# License

MIT

```
```
