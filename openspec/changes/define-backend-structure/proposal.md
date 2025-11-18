# Change: Define Backend Structure (Three-Layer Architecture)

## Why
明确项目分层与模块边界，避免代码混乱；将 AI 逻辑与传统后端逻辑解耦，便于独立迭代与测试。

## What Changes
- ADDED: 三层架构定义（数据层 → 业务层 → API 层）
- ADDED: `backend/ai_agents/` 与 `backend/normal_backend/` 双模块设计
- ADDED: `backend/shared/` 作为统一数据访问层
- ADDED: `app/` 作为 FastAPI 路由层，仅负责请求响应封装

## Impact
- Affected specs: 新增 `backend-structure` capability
- Affected code: 未来所有模块都按此结构组织
- 文档：新增 `ARCHITECTURE.md` 详细说明目录结构与数据流

## Breaking Changes
无（这是全新结构定义，不影响现有代码）
