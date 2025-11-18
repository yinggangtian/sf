## ADDED Requirements

### Requirement: 三层架构分离
系统 SHALL 采用"数据层 → 业务层 → API 层"三层架构，各层职责明确且单向依赖。

#### Scenario: API 层调用业务层
- WHEN FastAPI 路由接收请求
- THEN 通过依赖注入获取业务服务实例，不直接操作数据库

#### Scenario: 业务层访问数据层
- WHEN AI 或 Normal 模块需要读写数据
- THEN 通过 `backend/shared/db/` 统一接口访问 ORM

### Requirement: 双模块隔离
系统 SHALL 将 AI 智能模块与传统后端模块分离为 `backend/ai_agents/` 和 `backend/normal_backend/`，二者仅共享数据层。

#### Scenario: AI 模块独立演进
- WHEN 新增玄学算法或 RAG 能力
- THEN 仅修改 `backend/ai_agents/` 目录，不影响 `normal_backend`

#### Scenario: Normal 模块独立演进
- WHEN 新增支付/通知功能
- THEN 仅修改 `backend/normal_backend/` 目录，不影响 `ai_agents`

### Requirement: 统一数据访问
系统 SHALL 通过 `backend/shared/db/` 提供统一的 ORM 模型与 Session 工厂，所有模块共用。

#### Scenario: 跨模块数据一致性
- WHEN AI 模块保存占卜记录并关联用户 ID
- THEN 使用 `backend/shared/db/models.py` 中的 User 与 DivinationHistory 模型

### Requirement: FastAPI 路由仅封装
系统 SHALL 在 `app/routes/` 中仅做参数校验与响应封装，业务逻辑下沉到 `backend/` 层。

#### Scenario: 占卜请求路由
- WHEN 用户发起 POST /ai/divination
- THEN `app/routes/ai.py` 校验参数后调用 `backend/ai_agents/agents/orchestrator.py`

### Requirement: 模块测试独立
系统 SHALL 按模块拆分测试目录，集成测试验证跨模块协作。

#### Scenario: AI 模块单元测试
- WHEN 测试 Orchestrator 槽位填充逻辑
- THEN 在 `tests/test_ai_agents/` 中 mock DB 与工具调用

#### Scenario: 端到端集成测试
- WHEN 测试完整占卜流程
- THEN 在 `tests/test_integration/` 中启动真实 DB 与 Agent
