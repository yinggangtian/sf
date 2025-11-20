# Change: Align Liuren Engine With XLR Domain Doc

## Why
- 当前小六壬引擎只完成基础落宫/排盘，缺乏 XLR.md 中的完整计算链路与知识规则。
- 项目中仍沿用旧知识库结构，内容与最新文档不一致，导致解卦、寻物与 RAG 结果偏差。

## What Changes
- 更新小六壬计算逻辑：按 XLR.md 的 6 个阶段（定太极点→取时辰→定六兽→定六亲→LLM 用神→LLM 解读）产出结构化结果。
- 刷新知识库模型：引入文档里的六宫/六兽/六亲/地支/五行详细属性与提示，供引擎与 RAG 复用。
- 明确 LLM Prompt 协议：通过统一 JSON 输出，返回候选用神与规则解释，再做最终解读。
- 保持现有架构（Registry/Adapter/Engines），仅扩展实现与数据。

## Impact
- 规格：新增 `specs/xlr-liuren` 能力，描述全链路与知识要求；算法插件与 RAG 依赖。
- 代码：`backend/ai_agents/xlr/liuren/*`, `backend/ai_agents/services/knowledge_service.py`, 相关模型与测试。
- 数据：知识库 seed/同步脚本需要按 XLR.md 重写（同任务内落地）。
