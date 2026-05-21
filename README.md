# chat_agent

一个用于学习 Agent 基础工程化的极简中文助手项目。

项目支持：

- 命令行多轮对话
- FastAPI Web API
- OpenAI-compatible 模型调用
- 本地工具路由
- SQLite 知识库查询与写入
- API session/history 持久化
- 轻量 Web 前端
- 历史会话列表、会话删除、Markdown 消息渲染
- pytest 自动化测试

核心流程：

```text
用户输入 -> Agent 路由 -> 本地工具 / 知识库 / 普通 LLM -> 输出
```

## 目录结构

```text
.
├── agent.py                  # Agent 主流程：工具路由、知识库兜底、LLM 调用
├── cli.py                    # 命令行入口
├── service/
│   ├── api.py                # FastAPI 服务入口
│   ├── config.py             # 模型配置读取
│   ├── env.py                # .env 文件加载
│   ├── errors.py             # 统一异常类型
│   ├── knowledge_store.py    # SQLite 知识库数据层
│   ├── llm.py                # OpenAI-compatible 模型调用
│   ├── logger.py             # 日志初始化
│   ├── session_store.py      # session/history 持久化
│   └── tool_router.py        # 本地工具注册和匹配
├── skill/
│   ├── knowledge.py          # 知识库查询工具
│   ├── knowledge_write.py    # 知识库写入工具
│   └── time.py               # 当前时间工具
├── frontend/                 # Vite 原生前端
├── tests/                    # pytest 测试
├── requirements.txt          # 运行依赖
├── requirements-dev.txt      # 测试依赖
├── pytest.ini                # pytest 配置
└── .env.example              # 环境变量示例
```

运行时会自动创建本地数据和日志目录：

```text
database/
logs/
```

## 安装

创建虚拟环境并安装运行依赖：

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt
```

如需运行测试，再安装开发依赖：

```bash
venv/bin/pip install -r requirements-dev.txt
```

如需运行前端：

```bash
cd frontend
npm install
```

## 配置

复制示例配置：

```bash
cp .env.example .env
```

至少需要配置：

```bash
API_KEY="你的模型 API Key"
```

示例配置：

```bash
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL="qvq-max-2025-03-25"
REQUEST_TIMEOUT="30"
MAX_RETRIES="2"
LOG_LEVEL="INFO"
LOG_FILE="./logs/agent.log"
```

说明：

- 模型接口使用 OpenAI-compatible Chat Completions API。
- `BASE_URL` 和 `MODEL` 可以按实际服务商调整。

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

启动服务：

```bash
venv/bin/uvicorn service.api:app --host 127.0.0.1 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

聊天请求：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"现在几点？"}'
```

API 会返回 `session_id`，后续请求带上同一个 `session_id` 即可继续同一段历史：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"今天日期？","session_id":"上一次返回的 session_id"}'
```

读取历史会话：

```bash
curl http://127.0.0.1:8000/sessions/上一次返回的_session_id
```

列出最近会话：

```bash
curl http://127.0.0.1:8000/sessions
```

删除会话：

```bash
curl -X DELETE http://127.0.0.1:8000/sessions/要删除的_session_id
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

浏览器打开：

```text
http://127.0.0.1:5173
```

前端会调用 `/chat`，保存当前 `session_id`，刷新页面后自动加载历史消息。左侧会展示历史会话列表，支持切换会话、刷新列表和删除当前会话。

前端还支持：

- Enter 发送，Shift + Enter 换行
- 助手回复逐字显示
- 请求等待时显示思考动画
- 助手消息 Markdown 渲染

## 知识库用法

查询知识库：

```text
查询知识库 Python
搜索 FastAPI
```

写入知识库：

```text
添加知识：标题 | 内容 | 关键词
```

示例：

```text
添加知识：FastAPI | FastAPI 是一个用于构建 Python API 的 Web 框架。 | Python,API,Web
```

知识库默认保存在：

```text
database/knowledge.db
```

session/history 默认保存在：

```text
database/sessions.db
```

## 测试

运行全部测试：

```bash
venv/bin/python -m pytest -q
```

当前测试覆盖：

- `.env` 单行解析
- 知识库输入解析
- SQLite 知识库读写
- session/history 持久化
- SQLite 连接、事务和外键约束
- 工具路由
- Agent 主流程
- FastAPI 基础接口

测试使用临时数据库，不会污染真实的 `database/*.db`。

## 本地运行产物

```text
.env
venv/
logs/
database/*.db
frontend/node_modules/
frontend/dist/
```
