## ADDED Requirements
### Requirement: MVP Happy Path
系统 SHALL 在槽位齐全时直接路由 `xlr-liuren` 并返回解释输入包。

#### Scenario: 槽位齐全
- WHEN 请求包含 `num1,num2,gender,ask_time,timezone`
- THEN 调用适配器执行并返回包含 `plugin_result` 的解释输入包

### Requirement: 单轮追问与退出
系统 SHALL 在槽位缺失时进行一次追问；若用户仍未提供，列出缺失字段并结束本次流程。

#### Scenario: 缺失字段后追问
- WHEN 缺少 `num1`
- THEN 追问一次并等待补全

#### Scenario: 追问后仍缺失
- WHEN 追问后仍缺少关键信息
- THEN 返回缺失字段列表并退出

### Requirement: 路由策略（最小）
系统 SHALL 优先使用 `algorithm_hint`；否则根据意图关键词回退到 `xlr-liuren`。

#### Scenario: 提供 algorithm_hint
- WHEN `algorithm_hint = "xlr-liuren"`
- THEN 直接选择该适配器

#### Scenario: 无提示使用默认
- WHEN 未提供 `algorithm_hint`
- THEN 回退到 `xlr-liuren`

### Requirement: RAG 可选且不阻塞
系统 SHALL 允许 RAG 返回空列表，不得阻塞主流程。

#### Scenario: RAG 空
- WHEN RAG 查询失败/超时
- THEN 使用空列表继续返回解释输入包
