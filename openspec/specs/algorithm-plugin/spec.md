# Algorithm Plugin Abstraction

### Requirement: Adapter Interface
系统 SHALL 定义 `AlgorithmAdapter` 接口，包含 `id`, `describe()`, `validate(inputs)`, `run(inputs)`；`run` 返回统一结构 `{result,features?,confidence,meta?}`。

#### Scenario: 校验失败返回错误
- WHEN `validate(inputs)` 未通过
- THEN 返回字段错误列表并中止执行

#### Scenario: 规范输出
- WHEN `run(inputs)` 成功
- THEN 返回包含 `result` 与 `confidence(0..1)` 的对象

### Requirement: Registry
系统 SHALL 提供 `AlgorithmRegistry` 以注册/检索适配器，并支持列出可用算法元信息。

#### Scenario: 动态获取适配器
- WHEN Orchestrator 请求 `get("xlr-liuren")`
- THEN Registry 返回对应适配器实例或明确错误

### Requirement: 路由独立于实现
Orchestrator SHALL 仅依赖适配器接口；新增算法不影响 Orchestrator 与 Explainer 的实现。

#### Scenario: 新增算法不破坏编排
- WHEN 新算法通过 Registry 注册
- THEN 无需修改 Orchestrator 代码即可被路由并执行
