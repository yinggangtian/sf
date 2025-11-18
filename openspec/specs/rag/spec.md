# RAG 检索（pgvector）

### Requirement: 向量化与 Top-K 检索
系统 SHALL 使用 OpenAI Embedding 生成向量，并在 pgvector 上执行相似度检索，返回 Top-K 文本片段及源信息。

#### Scenario: 基于关键词/主题检索
- WHEN 提供 `topic/keywords` 与 `limit`
- THEN 返回不超过 `limit` 的相关片段（含 source/meta）

### Requirement: 降级策略
系统 SHALL 在超时或检索失败时降级为空列表，且不阻塞整体占卜流程。

#### Scenario: 检索超时
- WHEN RAG 查询超时
- THEN 返回空列表并在解释中注明“本次未引用典籍片段”

### Requirement: 离线索引构建
系统 SHOULD 提供离线脚本构建/更新索引（文本切分 → 向量写入）。

#### Scenario: 成功构建
- WHEN 运行索引构建脚本
- THEN 新增或更新 kb_document/kb_chunk/kb_embedding 并可被线上服务检索
