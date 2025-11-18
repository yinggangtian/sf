# Project Context

## Purpose
构建“玄学大师 Agent”后端与规格：支持小六壬占卜、RAG 引用典籍、Memory（用户画像与历史摘要）、可扩展工具与安全 Guardrails。以 OpenSpec 作为“当前真实能力（specs/）+ 变更计划（changes/）”的单一事实源，驱动从需求到实现的闭环。

## Tech Stack
- 语言/框架：Python（FastAPI/Starlette 可选）
- 数据访问：SQLAlchemy
- 数据库：Postgres + pgvector（向量检索）
- AI 调用：OpenAI Responses / Agents SDK
- 运行：uvicorn，本地可 ngrok 暴露

## Project Conventions

### Code Style
- Python 3.10+，类型提示优先（mypy 友好）
- 小而清晰的模块；单一职责
- Public API 稳定，内部可迭代

### Architecture Patterns
**三层架构 + 双模块设计**（详见 `ARCHITECTURE.md`）：

1. **数据层**：`backend/shared/db/` 统一 ORM 与 Session
2. **业务层**：
   - `backend/ai_agents/`：Agent 编排、算法、RAG、Prompts
   - `backend/normal_backend/`：Auth、User、Payment、Notification
3. **API 层**：`app/` FastAPI 路由，依赖注入，不含业务逻辑

**核心模式**：
- 双 Agent 分层：Orchestrator（意图/槽位/算法路由）与 Explainer（解读生成/评审/输出）
- 算法插件化：`AlgorithmAdapter` + `AlgorithmRegistry`
- RAG 解耦：离线构建索引，在线 Top-K 检索
- Memory：长期（profile/summary）+ 短期（会话）
- 模块独立：AI 模块与 Normal 模块仅共享数据层，互不依赖

### Testing Strategy
- 单元：算法引擎、RAG 检索、工具 I/O Schema 校验
- 集成：最小闭环（起卦 → RAG → 解读 → 保存）
- 回归：变更通过 `openspec` 的场景验证对齐

### Git Workflow
- 常规 Git Flow：feature 分支 → PR → Review
- 变更先走 `openspec/changes/` 提案，获批再实现

## Domain Context
- 小六壬：两数字 + 时间 + 性别 → 卦象结构、关键词、特征
- 解释需要：结合 RAG 经典与用户画像/历史摘要，生成“人话”与免责声明
- Guardrails：输入合法性与输出措辞安全

## Important Constraints
- `ask_time` 不可晚于当前时间；数字范围 1~9；性别枚举
- 输出避免绝对化与敏感承诺；强制附加免责声明
- RAG 超时时允许降级为空结果

## External Dependencies
- OpenAI API（Responses / Agents）
- Postgres（含 pgvector 扩展）
- 可选：Redis 作为缓存
