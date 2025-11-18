# Guardrails（输入/输出安全）

### Requirement: 输入校验
系统 SHALL 校验 `num1/num2 ∈ [1,9]`，`ask_time ≤ now()`（含时区），`gender ∈ {M,F,Unknown}`，过长问题截断并提示。

#### Scenario: 非法时间
- WHEN `ask_time` 晚于当前时间
- THEN 返回错误并要求用户提供合法时间

#### Scenario: 非法时区
- WHEN `timezone` 不在受支持列表
- THEN 返回错误并提示可用时区格式（IANA 名称）

#### Scenario: 输入过长被截断
- WHEN `question` 超过上限（例如 1,000 字符）
- THEN 截断为上限长度并在响应中附带警告

### Requirement: 输出安全
系统 SHALL 禁止绝对化与敏感承诺类措辞，统一添加免责声明，必要时对文本进行重写。

#### Scenario: 风险措辞过滤
- WHEN 生成结果包含敏感承诺
- THEN 过滤/替换并附加风险提示与免责声明

### Requirement: 流式输出降级
系统 MAY 在流式生成遇到违规片段时截断当前流并回退到安全模板重写。

#### Scenario: 流式违规截断
- WHEN 检测到违规短语
- THEN 终止当前流并快速返回安全版输出
