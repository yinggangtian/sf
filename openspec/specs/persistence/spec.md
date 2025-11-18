# 持久化（历史与记忆）

### Requirement: 占卜历史存储
系统 SHALL 将每次占卜写入 `divination_history`：包含 question、intent、num1/num2、gender、ask_time、liuren_result、rag_context、answer、feedback?。

#### Scenario: 成功落库
- WHEN Explainer 生成最终回答
- THEN 写入一条历史记录并返回保存状态

### Requirement: 用户画像与对话摘要
系统 SHALL 读/写 `user_profile` 与 `conversation_summary`，并在占卜完成后按策略更新摘要。

#### Scenario: 更新摘要
- WHEN 完成一次较完整占卜
- THEN 调用 `update_conversation_summary` 写入新的摘要文本

### Requirement: 历史查询
系统 SHALL 支持按 `user_id` 分页查询历史记录，并可按时间/类型过滤。

#### Scenario: 最近记录
- WHEN 请求最近 N 条记录
- THEN 按时间倒序返回 N 条简要信息
