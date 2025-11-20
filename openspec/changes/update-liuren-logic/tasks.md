## 1. Knowledge Base
- [ ] 1.1 依据 XLR.md 重建六宫/六兽/六亲/地支/五行静态数据（含属性字段）
- [ ] 1.2 扩展 `KnowledgeService` 以一次性加载新版结构并提供查询/缓存

## 2. 算法实现
- [ ] 2.1 更新 PaipanEngine：实现定太极点、取时辰阴阳顺排、六兽/六亲映射与结构化输出
- [ ] 2.2 更新 JieguaEngine：按新知识分析、寻物方位、体用关系
- [ ] 2.3 新增 LLM Prompt/工具流程：解析用神、生成最终解读 JSON

## 3. 验证
- [ ] 3.1 添加/更新单元与集成测试，覆盖落宫、阴阳顺排、六兽/六亲、LLM 接口
- [ ] 3.2 运行 `pytest tests/integration/test_orchestrator_flow.py -k liuren` 与相关单测确保通过
