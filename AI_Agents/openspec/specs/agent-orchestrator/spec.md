# Agent Orchestrator

### Requirement: Intent & Slot Filling
系统 SHALL 从用户自然语言中识别意图并抽取槽位：`num1,num2,gender,ask_time,timezone,location,question_type,algorithm_hint`。缺失时应追问以补齐。

#### Scenario: 完整槽位直接进入算法
- WHEN 用户输入包含完整槽位（两数字、性别、时间、时区）
- THEN 系统直接路由到指定算法适配器执行

#### Scenario: 槽位缺失触发追问
- WHEN 缺少任一关键槽位
- THEN 系统向用户发出最小必要澄清问题并等待补全

### Requirement: 槽位追问退出条件
系统 SHALL 限制追问轮次（例如 1 次），若仍无法补齐，返回缺失字段列表并结束本次流程。

#### Scenario: 达到最大追问轮次
- WHEN 已追问 1 次但 `num1/num2` 仍缺失
- THEN 返回缺失字段列表并终止当前会话流程

### Requirement: Algorithm Routing
系统 SHALL 根据 `algorithm_hint` 或意图分类在 `AlgorithmRegistry` 中选择合适的算法适配器（如 `xlr-liuren`）。

#### Scenario: 显式算法提示
- WHEN 请求携带 `algorithm_hint="xlr-liuren"`
- THEN 系统优先选用对应适配器

#### Scenario: 关键词路由
- WHEN 未提供 `algorithm_hint`
- THEN 系统基于意图推断（如“六壬/姻缘/寻物”）选择默认适配器或向用户澄清

### Requirement: RAG 与工具协调
系统 MAY 在算法执行并行/串行阶段触发 RAG 检索、读取用户画像与历史摘要，合并为解释输入包。

#### Scenario: 需要典籍支撑
- WHEN 问题类型需要经典引用
- THEN 触发 `rag_search` 获取 Top-K 片段并注入解释上下文

### Requirement: 解释输入包组装
系统 SHALL 组装并传递如下对象给 Explainer：`{question,intent,slots,algorithm_id,plugin_result,rag_chunks?,profile?,history_summary?}`。

#### Scenario: 包含所有可用上下文
- WHEN 画像/摘要/RAG 可用
- THEN 解释输入包包含这些字段；不可用时对应字段可省略
