# Change: Implement Agent Orchestrator MVP

## Why
将“意图 + 槽位 → 算法 → 解释输入包”的最小闭环落地，作为后续扩展（RAG/评审/并行）的基础。

## What Changes
- ADDED: Orchestrator 入口与最小 Happy Path（完整槽位 → `xlr-liuren` → 解释输入包）
- ADDED: 槽位缺失的单轮追问与退出条件
- ADDED: 基于 `algorithm_hint` 与关键词的路由策略（最小实现）
- ADDED: 失败与降级策略：RAG 可为空、验证失败返回字段错误

## Impact
- Affected specs: `agent-orchestrator`
- Affected code: 预期在 `app/` 增加 Orchestrator 模块与测试用例
