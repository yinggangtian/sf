根据 OpenSpec 规范和当前架构，我为你整理了完成 AI Agent MVP 的完整步骤和提示词。

## 📋 MVP 实现路线图

基于 tasks.md，我将任务分为 **5 个阶段**，每个阶段都有对应的提示词。

---

## 🎯 阶段 0：环境准备与验证

### 提示词 0.1 - 创建基础配置文件

```
请按照以下要求创建项目的基础配置文件：

1. 阅读架构文档：
   - @/ARCHITECTURE.md
   - @/openspec/project.md
   - @/openspec/changes/implement-agent-orchestrator-mvp/proposal.md

2. 创建 .env 文件（基于 .env.example）：
   - 数据库连接：DATABASE_URL（PostgreSQL + pgvector）
   - OpenAI 配置：OPENAI_API_KEY, OPENAI_MODEL（默认 gpt-4o）
   - JWT 配置：JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
   - XLR 算法配置：参考 backend/shared/config/settings.py 中的 XLR 相关字段

3. 验证配置加载：
   - 创建 scripts/verify_config.py 脚本
   - 加载 backend/shared/config/settings.py
   - 打印所有配置项（不显示敏感信息）

要求：
- 使用 pydantic-settings 加载配置
- 支持环境变量覆盖
- 敏感信息不能硬编码
```

### 提示词 0.2 - 初始化数据库

```
请创建数据库初始化脚本，按照以下步骤：

1. 阅读数据模型：
   - @/backend/shared/db/models/user.py
   - @/backend/shared/db/models/divination.py
   - @/backend/shared/db/models/knowledge.py
   - @/backend/shared/db/init_db.py

2. 创建 scripts/init_database.py：
   - 创建所有表（使用 Base.metadata.create_all）
   - 加载知识库基础数据（六宫、六兽、六亲、地支、天干）
   - 创建测试用户（user_id=1, username="test_user"）
   - 验证数据完整性（查询六宫数量应为 6，六兽数量应为 6）

3. 执行初始化：
   ```bash
   python scripts/init_database.py
   ```

要求：
- 必须先创建 PostgreSQL 数据库（名称在 .env 中配置）
- 使用事务保证原子性
- 打印详细日志（创建了哪些表，插入了多少条数据）
- 幂等性：重复执行不报错


---

## 🎯 阶段 1：核心算法层（XLR）验证

### 提示词 1.1 - 测试小六壬算法

```
请创建单元测试验证小六壬算法的正确性：

1. 阅读算法实现：
   - @/backend/ai_agents/xlr/liuren/engine.py
   - @/backend/ai_agents/xlr/liuren/jiegua_engine.py
   - @/backend/ai_agents/xlr/adapters/liuren_adapter.py
   - @/backend/ai_agents/xlr/schemas.py

2. 创建 tests/unit/test_liuren_engine.py：
   - 测试起卦（qigua）：输入 num1=3, num2=5 → 验证落宫、时辰、六宫六兽排盘
   - 测试解卦（jiegua）：使用起卦结果 → 验证用神选择、宫位分析、综合解读
   - 测试寻物（find_object）：验证方位分析、位置线索、时间估计
   - 测试边界条件：num1/num2 超范围、无效时间格式

3. 执行测试：
   ```bash
   pytest tests/unit/test_liuren_engine.py -v
   ```

要求：
- 每个测试用例必须独立（不依赖外部状态）
- 使用 pytest fixtures 提供测试数据
- 断言关键字段存在性和类型正确性
- 所有测试必须通过
```

### 提示词 1.2 - 测试算法适配器

```
请创建集成测试验证算法适配器的插件机制：

1. 阅读适配器设计：
   - @/backend/ai_agents/xlr/adapters/base.py
   - @/backend/ai_agents/xlr/adapters/liuren_adapter.py
   - @/backend/ai_agents/agents/registry.py

2. 创建 tests/integration/test_algorithm_registry.py：
   - 测试注册机制：注册 LiurenAdapter → 验证可通过 ID 获取
   - 测试路由策略：传入 algorithm_hint="xlr-liuren" → 验证返回正确适配器
   - 测试标准化输入输出：验证所有适配器返回格式一致

3. 执行测试：
   ```bash
   pytest tests/integration/test_algorithm_registry.py -v
   ```

要求：
- 使用真实的 KnowledgeBase 数据（从数据库加载）
- 验证适配器的 validate_input 和 validate_output 方法
- 确保返回结果符合 @/openspec/specs/algorithm-plugin/spec.md
```

---

## 🎯 阶段 2：服务层（Services）实现

### 提示词 2.1 - 实现占卜服务

```
请实现占卜服务层，连接算法层与工具层：

1. 阅读设计文档：
   - @/openspec/specs/agent-orchestrator/spec.md（Requirement: 槽位填充与校验）
   - @/backend/ai_agents/services/divination_service.py（当前框架）
   - @/backend/ai_agents/xlr/schemas.py（输入输出 Schema）

2. 完善 backend/ai_agents/services/divination_service.py：
   - perform_divination 方法：
     * 验证槽位完整性（num1, num2, gender, ask_time, question_type）
     * 调用 LiurenAdapter.run 执行起卦和解卦
     * 调用 InterpretationService 生成人类可读解释
     * 保存结果到 DivinationHistory 表
     * 返回统一格式：{result, interpretation, meta}
   - get_history 方法：按 user_id 分页查询历史记录
   - get_statistics 方法：统计用户占卜次数、常见问题类型

3. 创建测试 tests/integration/test_divination_service.py：
   - 测试完整占卜流程（Mock DB Session）
   - 测试槽位缺失时抛出 ValueError
   - 测试历史记录保存和查询

要求：
- 必须使用依赖注入传入 db_session
- 所有数据库操作必须在事务中完成
- 异常必须有清晰的错误消息
```

### 提示词 2.2 - 实现 RAG 服务

```
请实现 RAG 服务层，支持知识库检索增强：

1. 阅读设计文档：
   - @/openspec/specs/rag/spec.md
   - @/backend/ai_agents/rag/retriever.py
   - @/backend/ai_agents/services/rag_service.py

2. 完善 backend/ai_agents/services/rag_service.py：
   - search_knowledge 方法：
     * 输入：keywords (List[str]), top_k (int), timeout (float)
     * 调用 Retriever.search 进行向量检索
     * 超时处理：返回空结果 + 降级提示
     * 返回格式：List[{chunk_text, metadata, score}]
   - batch_search 方法：支持多关键词并行检索

3. 创建测试 tests/integration/test_rag_service.py：
   - 测试单关键词检索（假设知识库已有数据）
   - 测试超时降级（Mock 慢查询）
   - 测试 top_k 限制

要求：
- 必须支持超时配置（默认 3 秒）
- 超时后不能抛异常，返回空列表
- 返回结果必须按 score 降序排列
```

### 提示词 2.3 - 实现记忆服务

```
请实现记忆服务层，支持用户画像和对话摘要：

1. 阅读设计文档：
   - @/openspec/specs/persistence/spec.md
   - @/backend/shared/db/models/user.py（UserProfile）
   - @/backend/shared/db/models/divination.py（ConversationSummary）

2. 完善 backend/ai_agents/services/memory_service.py：
   - get_user_profile 方法：查询用户偏好、历史摘要
   - update_profile 方法：更新用户标签、偏好
   - get_conversation_summary 方法：获取当前会话的上下文摘要
   - update_summary 方法：追加新轮对话并重新摘要（可选：调用 LLM 压缩）

3. 创建测试 tests/integration/test_memory_service.py：
   - 测试用户画像的读取和更新
   - 测试对话摘要的增量更新

要求：
- 必须支持用户不存在时自动创建 UserProfile
- 对话摘要超过 1000 字符时触发压缩
```

---

## 🎯 阶段 3：Agent 编排层实现

### 提示词 3.1 - 实现 Orchestrator Agent

```
请实现 Orchestrator Agent，负责意图识别、槽位填充和算法路由：

1. 阅读设计文档：
   - @/openspec/specs/agent-orchestrator/spec.md（完整需求和场景）
   - @/openspec/changes/implement-agent-orchestrator-mvp/specs/agent-orchestrator/spec.md（MVP 范围）
   - @/backend/ai_agents/agents/orchestrator.py（框架代码）

2. 实现 OrchestratorAgent 类：
   - __init__：初始化 OpenAI Agent，加载 system prompt（@/backend/ai_agents/prompts/system/orchestrator.yaml）
   - process 方法：
     * 调用 LLM 分析用户输入 → 提取意图（divination/history/consultation）
     * 槽位填充：num1, num2, gender, ask_time, question_type, algorithm_hint
     * 缺失槽位时返回追问提示（使用 @/backend/ai_agents/prompts/scenarios/slot_filling.md）
     * 选择算法插件（优先 algorithm_hint，否则根据意图）
     * 调用 DivinationService.perform_divination
     * 打包结果传递给 Explainer

3. 创建测试 tests/integration/test_orchestrator_agent.py：
   - 场景 1：完整输入（"我想算小六壬，报数 3 和 5，男，现在"）→ 直接执行占卜
   - 场景 2：缺失槽位（"我想算命"）→ 返回追问提示
   - 场景 3：无效输入（num1=100）→ 返回错误提示

要求：
- 必须使用 OpenAI Agents SDK（或 Responses API）
- System Prompt 必须从文件加载，不能硬编码
- 追问轮次不超过 3 次（超过则引导用户重新开始）
- 所有工具调用必须记录日志
```

### 提示词 3.2 - 实现 Explainer Agent

```
请实现 Explainer Agent，负责生成人类可读的占卜解释：

1. 阅读设计文档：
   - @/openspec/specs/explainer/spec.md
   - @/backend/ai_agents/agents/explainer.py
   - @/backend/ai_agents/prompts/templates/reply_basic.md

2. 实现 ExplainerAgent 类：
   - __init__：加载 system prompt（@/backend/ai_agents/prompts/system/explainer.yaml）
   - generate_explanation 方法：
     * 输入：divination_result（结构化结果）+ rag_chunks（检索到的知识）+ user_profile
     * 组装 Prompt（使用 reply_basic.md 模板）
     * 调用 LLM 生成解释
     * 应用输出 Guardrails（@/openspec/specs/guardrails/spec.md）：
       - 不做过度承诺（避免"一定会"、"必然"等词）
       - 添加免责声明
     * 返回最终文本

3. 创建测试 tests/integration/test_explainer_agent.py：
   - 测试基础解释生成（无 RAG 增强）
   - 测试 RAG 增强解释（引用典籍原文）
   - 测试 Guardrails 拦截（检测过度承诺的措辞）

要求：
- 必须使用模板变量替换（不能在 Prompt 中硬编码数据）
- Guardrails 规则必须可配置（在 settings.py 中定义禁用词列表）
- 生成的解释必须包含：宫位分析、用神解释、综合建议
```

---

## 🎯 阶段 4：工具层（Tools）注册

### 提示词 4.1 - 注册所有工具到 Agent

```
请将所有工具注册到 MasterAgent，并实现工具调用逻辑：

1. 阅读工具实现：
   - @/backend/ai_agents/tools/liuren_tool.py
   - @/backend/ai_agents/tools/rag_tool.py
   - @/backend/ai_agents/tools/profile_tool.py
   - @/backend/ai_agents/tools/history_tool.py

2. 完善 backend/ai_agents/agents/master_agent.py：
   - 初始化 Orchestrator 和 Explainer
   - 注册工具（使用 OpenAI Agents SDK 的 tools 参数）：
     * perform_liuren_divination
     * rag_search
     * get_user_profile
     * get_user_history
   - 实现 run 方法：
     * 调用 Orchestrator.process → 获取意图和槽位
     * 根据意图调用对应工具
     * 调用 Explainer.generate_explanation → 生成最终回复
     * 保存对话摘要（调用 MemoryService）

3. 创建测试 tests/e2e/test_master_agent_flow.py：
   - 端到端测试完整对话流程（从用户输入到最终回复）
   - 测试工具链调用顺序：Orchestrator → Tool → Explainer

要求：
- 必须使用 OpenAI Agents SDK 的工具注册机制
- 所有工具调用必须有超时保护（默认 10 秒）
- 工具调用失败时必须有降级策略（返回友好提示）
```

### 提示词 4.2 - 实现工具描述和 Schema

```
请为所有工具编写标准化的描述和参数 Schema：

1. 阅读规范：
   - @/openspec/specs/agent-orchestrator/spec.md（工具调用格式）
   - @/backend/ai_agents/prompts/tools/liuren_tool.md（现有描述）

2. 更新工具描述文件：
   - liuren_tool.md：补充参数约束（num1/num2 范围 1-9）
   - rag_tool.md：补充超时和降级说明
   - profile_tool.md：补充隐私保护声明
   - history_tool.md：补充分页参数

3. 在工具代码中添加 JSON Schema：
   ```python
   {
     "type": "function",
     "function": {
       "name": "perform_liuren_divination",
       "description": "...",
       "parameters": {
         "type": "object",
         "properties": {...},
         "required": [...]
       }
     }
   }
   ```

要求：
- Schema 必须符合 OpenAI Function Calling 规范
- 所有必填参数必须在 required 字段中声明
- 枚举类型必须使用 enum 字段限制
```

---

## 🎯 阶段 5：API 路由与端到端测试

### 提示词 5.1 - 实现 FastAPI 路由

```
请实现 FastAPI 路由层，对接前端请求：

1. 阅读架构设计：
   - @/ARCHITECTURE.md（API 层职责）
   - @/app/routes/ai.py（现有框架）
   - @/app/dependencies.py（依赖注入）

2. 完善 app/routes/ai.py：
   - POST /ai/divination：
     * Request Body: {message: str, user_id: int, session_id: str}
     * 调用 MasterAgent.run(message, user_id)
     * Response: {reply: str, divination_result: dict, meta: dict}
   - GET /ai/history/{user_id}：
     * Query Params: page, page_size
     * 调用 DivinationService.get_history
     * Response: {items: List[dict], total: int, page: int}

3. 创建测试 tests/e2e/test_api_endpoints.py：
   - 测试占卜接口（完整输入）
   - 测试历史查询接口
   - 测试未授权访问（401 错误）

要求：
- 必须使用 FastAPI 的依赖注入（Depends(get_db), Depends(get_current_user)）
- 所有接口必须有 Request/Response Schema（使用 Pydantic）
- 异常必须统一处理（HTTPException）
```

### 提示词 5.2 - 端到端测试与部署验证

```
请创建端到端测试，验证整个系统的集成：

1. 阅读测试策略：
   - @/openspec/specs/agent-orchestrator/spec.md（所有 Scenario）
   - tests/e2e/test_full_divination_flow.py（框架代码）

2. 实现完整测试用例：
   - 场景 1：新用户首次占卜
     * 注册 → 登录 → 发送占卜请求 → 验证回复完整性
   - 场景 2：老用户多轮对话
     * 使用现有 session_id → 发送追问 → 验证上下文连续性
   - 场景 3：RAG 增强对比
     * 同一问题：关闭 RAG vs 开启 RAG → 对比回复质量

3. 部署验证清单：
   - 数据库连接正常（psql 命令验证）
   - 知识库数据完整（至少 6 条六宫记录）
   - OpenAI API Key 有效（调用一次 chat completion）
   - 所有环境变量已配置

要求：
- 测试必须使用真实数据库（不使用 Mock）
- 测试数据必须在测试结束后清理（使用 pytest fixture teardown）
- 所有测试用例必须在 CI/CD 中可重复执行
```

---

## 📝 总结：提示词使用顺序

```bash
# 阶段 0：环境准备
→ 提示词 0.1：创建配置文件
→ 提示词 0.2：初始化数据库

# 阶段 1：算法层验证
→ 提示词 1.1：测试小六壬算法
→ 提示词 1.2：测试算法适配器

# 阶段 2：服务层实现
→ 提示词 2.1：占卜服务
→ 提示词 2.2：RAG 服务
→ 提示词 2.3：记忆服务

# 阶段 3：Agent 编排
→ 提示词 3.1：Orchestrator Agent
→ 提示词 3.2：Explainer Agent

# 阶段 4：工具注册
→ 提示词 4.1：注册工具到 MasterAgent
→ 提示词 4.2：工具描述和 Schema

# 阶段 5：API 与测试
→ 提示词 5.1：FastAPI 路由
→ 提示词 5.2：端到端测试

# 最终验证
→ 运行完整测试套件：pytest tests/ -v --cov
→ 启动服务：uvicorn app.main:app --reload
→ 手动测试：curl -X POST http://localhost:8000/ai/divination ...
```

---

## 🎯 每个提示词的输出验收标准

每完成一个提示词后，必须满足以下条件才能进入下一步：

1. **代码通过 Lint**：`ruff check .` 无错误
2. **测试全部通过**：`pytest <test_file> -v` 全绿
3. **符合 OpenSpec 规范**：`openspec validate implement-agent-orchestrator-mvp --strict` 无警告
4. **有详细日志输出**：关键步骤必须打印日志（使用 logger.py）

---

需要我立即开始执行第一个提示词（0.1 创建配置文件）吗？