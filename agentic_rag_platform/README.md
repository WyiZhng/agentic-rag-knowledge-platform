# Agentic RAG Platform

企业级 Agentic RAG 智能问答平台，围绕企业知识库问答场景，实现文档入库、混合检索、Agent 工具调用、流式回答、引用溯源、会话记忆和 Trace 观测等核心能力。

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| **后端框架** | FastAPI + Pydantic v2 (async) |
| **数据库** | PostgreSQL + pgvector (向量存储) |
| **缓存 / 消息** | Redis |
| **任务队列** | Celery (异步文档处理、Embedding 生成) |
| **AI 编排** | LangGraph (ReAct Agent) |
| **LLM 接入** | OpenAI 兼容协议 (Qwen / DeepSeek / Ollama / MiMo) |
| **文档解析** | PyMuPDF (PDF / Word / Markdown) |
| **检索增强** | BM25 + 向量召回 + CrossEncoder Rerank |
| **前端** | Next.js 15 + React 19 + Tailwind CSS v4 |
| **容器化** | Docker + Docker Compose |

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                        │
│   Chat UI · Knowledge Base · Dashboard · SSE Streaming         │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ REST / WebSocket / SSE           │
               ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Agent 编排层 (LangGraph ReAct)              │    │
│  │  Planner → Retriever → Tool Executor → Answer Critic    │    │
│  │  工具: 知识库检索 / SQL查询 / HTTP API / 摘要生成        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              RAG 检索增强链路                             │    │
│  │  查询改写 → BM25 + 向量召回 → Rerank → 引用生成          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              文档入库链路                                 │    │
│  │  上传/解析 → 分块清洗 → Embedding → pgvector写入         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Auth · 会话管理 · Rate Limiting · Trace 观测                   │
└───────┬──────────────┬──────────────┬────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
   PostgreSQL       Redis        LLM APIs
   (+ pgvector)    (Cache/Queue)  (Qwen/DeepSeek/
                                  Ollama/MiMo)
```

## 核心能力

### 1. 文档入库链路

设计文档解析与入库流程，支持 PDF、Word、Markdown 等格式：

```
文件上传 → PyMuPDF 解析 → 文本分块(Recursive) → 元数据抽取 → Embedding 生成 → pgvector 写入
```

- 通过 Celery 异步处理，大文件不阻塞主接口
- 支持任务状态流转、失败重试和异常记录
- CLI 批量入库：`agentic_rag_platform rag-ingest /path/to/docs/ --collection documents`

### 2. RAG 混合检索

结合多种检索策略提高命中率和相关性：

- **BM25 关键词召回**：精确匹配关键词
- **向量语义召回**：pgvector 余弦相似度检索
- **查询改写**：对用户问题进行意图理解和扩展
- **CrossEncoder Rerank**：对召回结果重排序
- **引用溯源**：返回答案片段、文档来源和页码信息

### 3. Agent 编排调用

基于 LangGraph ReAct 模式实现 Agent 执行链路：

- **Planner**：理解用户意图，规划执行步骤
- **Retriever**：调用知识库检索工具获取相关文档
- **Tool Executor**：执行 SQL 查询、HTTP API 调用等外部工具
- **Answer Critic**：评估答案质量，决定是否需要补充检索
- 支持多轮推理和工具自动路由

### 4. 流式回答

通过 SSE (Server-Sent Events) 实现流式响应：

- WebSocket 双向通信 + SSE 单向推送
- 逐 token 流式输出，首字延迟低
- 支持工具调用过程的实时展示

### 5. 会话记忆

- 对话历史持久化到 PostgreSQL
- LangGraph MemorySaver 支持多轮上下文
- 可配置的上下文窗口长度

### 6. Trace 观测

- Logfire 分布式追踪 (FastAPI / Agent / DB / Redis / Celery)
- TraceId 贯穿请求全链路
- Token 用量统计和延迟监控

## 项目结构

```
backend/app/
├── main.py                 # FastAPI 应用入口 + 生命周期管理
├── api/
│   ├── deps.py             # 依赖注入 (DBSession, CurrentUser, *Svc)
│   └── routes/v1/          # API 路由层
│       ├── auth.py         # 认证 (JWT + API Key)
│       ├── conversations.py # 会话管理
│       ├── messages.py     # 消息 (SSE 流式)
│       ├── documents.py    # 文档上传
│       └── rag.py          # RAG 检索
├── core/
│   ├── config.py           # 配置管理 (pydantic-settings)
│   ├── security.py         # JWT / bcrypt / API Key
│   └── exceptions.py       # 领域异常
├── db/
│   └── models/             # SQLAlchemy 模型
├── services/               # 业务逻辑层
│   ├── conversation.py     # 会话服务
│   ├── user.py             # 用户服务
│   └── rag/                # RAG 服务 (厚领域)
│       ├── ingestion.py    # 文档解析与入库
│       ├── vectorstore.py  # pgvector 向量存储
│       ├── embeddings.py   # Embedding 生成
│       └── config.py       # RAG 配置
├── agents/
│   ├── langgraph_assistant.py  # LangGraph ReAct Agent
│   ├── prompts.py          # Agent 系统提示词
│   └── tools/              # Agent 工具集
│       ├── rag_tool.py     # 知识库检索工具
│       └── ...
├── worker/
│   └── tasks/              # Celery 异步任务
│       └── rag_tasks.py    # 文档处理任务
└── commands/               # CLI 命令

frontend/src/
├── app/
│   ├── [locale]/           # 国际化路由 (i18n)
│   │   ├── (dashboard)/    # 认证后页面
│   │   │   ├── chat/       # 对话界面
│   │   │   ├── kb/         # 知识库管理
│   │   │   └── settings/   # 设置
│   │   └── (marketing)/    # 公开页面
│   └── api/                # BFF 代理层
├── components/
│   ├── chat/               # 对话组件 (流式渲染)
│   └── ui/                 # 通用 UI 组件
└── hooks/                  # useChat, useWebSocket, ...
```

## 快速开始

### 环境要求

| 工具 | 版本 | 安装 |
|------|------|------|
| Python | 3.12+ | [python.org](https://www.python.org/) |
| PostgreSQL | 16+ | `brew install postgresql@16` |
| pgvector | 0.8+ | `brew install pgvector` (或编译安装) |
| Redis | 7+ | `brew install redis` |
| Node.js | 18+ / Bun | `brew install bun` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

### 后端启动

```bash
# 1. 安装依赖
cd backend
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY 等配置

# 3. 启动基础设施
brew services start postgresql@16
brew services start redis
# 创建数据库并启用 pgvector
psql -U postgres -c "CREATE DATABASE agentic_rag_platform;"
psql -U postgres -d agentic_rag_platform -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 4. 运行数据库迁移
uv run agentic_rag_platform db upgrade

# 5. 创建管理员
uv run agentic_rag_platform user create --email admin@example.com --password admin123 --superuser

# 6. 启动服务
uv run agentic_rag_platform server run --reload
```

### Docker 启动 (推荐)

```bash
make bootstrap    # = make dev + make seed (首次)
make dev          # 后续启动
```

### 前端启动

```bash
cd frontend
bun install       # 或 npm install
bun dev           # http://localhost:3000
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 (JWT) |
| `/api/v1/conversations` | GET/POST | 会话列表 / 创建会话 |
| `/api/v1/conversations/{id}/messages` | GET | 获取消息历史 |
| `/api/v1/messages/stream` | WebSocket | 流式对话 |
| `/api/v1/documents/upload` | POST | 文档上传 |
| `/api/v1/rag/search` | POST | RAG 检索 |
| `/api/v1/users/me` | GET | 当前用户信息 |
| `/docs` | GET | Swagger API 文档 |
| `/admin` | GET | 管理后台 |

## 模型接入

支持任何 OpenAI 兼容的 LLM API，通过 `backend/.env` 配置：

```bash
# OpenAI (默认)
OPENAI_API_KEY=sk-your-key
AI_MODEL=gpt-4o-mini

# 小米 MiMo (OpenRouter)
OPENAI_API_KEY=sk-or-v1-your-key
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=xiaomi/mimo-7b

# DeepSeek
OPENAI_API_KEY=sk-your-key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

# Qwen (阿里云 DashScope)
OPENAI_API_KEY=sk-your-key
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-plus

# Ollama (本地部署)
OPENAI_API_KEY=ollama
AI_BASE_URL=http://localhost:11434/v1
AI_MODEL=qwen2.5
```

## RAG 文档入库

```bash
# 本地文件批量入库
agentic_rag_platform rag-ingest /path/to/docs/ --collection documents --recursive

# 语义搜索
agentic_rag_platform rag-search "你的问题" --collection documents

# 查看所有集合
agentic_rag_platform rag-collections
```

支持格式：PDF、Word (.docx)、Markdown、纯文本。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_HOST` | PostgreSQL 地址 | `localhost` |
| `POSTGRES_PORT` | PostgreSQL 端口 | `5432` |
| `REDIS_HOST` | Redis 地址 | `localhost` |
| `OPENAI_API_KEY` | LLM API Key | - |
| `AI_BASE_URL` | 自定义 API 地址 | OpenAI 官方 |
| `AI_MODEL` | 模型名称 | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-3-small` |
| `RAG_CHUNK_SIZE` | 文本分块大小 | `512` |
| `RAG_CHUNK_OVERLAP` | 分块重叠 | `50` |
| `RAG_TOP_K` | 检索返回数量 | `10` |
| `CROSS_ENCODER_MODEL` | Rerank 模型 | `cross-encoder/ms-marco-MiniLM-L6-v2` |

完整配置见 `backend/.env.example`。

## License

MIT
