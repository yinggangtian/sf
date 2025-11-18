# Explainer (结构化结果 → 人类可读)

### Requirement: Prompt 组装
系统 SHALL 基于模板（基础/高级）将 `plugin_result`、RAG 片段、用户画像、历史摘要与原始问题合成 Prompt。

#### Scenario: 基础模板
- WHEN 无高级模板需求
- THEN 使用基础模板并限制长度、避免冗余

### Requirement: LLM-as-a-Judge（可选）
系统 MAY 在生成初稿后进行自评与结构检查，必要时进行一次改写迭代（受限于最大迭代次数与成本）。

#### Scenario: 自评触发重写
- WHEN 初稿存在逻辑不自洽/缺少必要引用
- THEN 触发一次重写并输出合规版本

### Requirement: 输出 Guardrails 与免责声明
系统 SHALL 在最终输出阶段统一过滤禁词、避免绝对化表述，并强制附加免责声明。

#### Scenario: 绝对化措辞被替换
- WHEN 生成结果包含“必然/一定会”等绝对表达
- THEN 系统改写为概率性表述并附加提示
