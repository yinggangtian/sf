# 端到端测试文档

## 概述

本文档说明如何运行完整的端到端测试，验证整个系统从用户请求到最终响应的集成。

## 测试场景

### 场景 1：用户首次占卜

#### 1.1 完整槽位直接进入算法
- **测试函数**: `test_scenario_1_first_time_divination_complete_slots`
- **验证内容**:
  - 用户提供完整槽位（两个数字、性别、问题类型）
  - 系统直接执行算法，返回完整占卜结果
  - 数据库正确保存占卜记录
  - 响应包含完整的结构化数据

#### 1.2 槽位缺失触发追问
- **测试函数**: `test_scenario_1_first_time_divination_missing_slots`
- **验证内容**:
  - 用户提供不完整的槽位信息
  - 系统返回追问，要求补充必要信息
  - 状态为 `clarification_needed`
  - 未创建占卜结果

### 场景 2：用户多轮对话

- **测试函数**: `test_scenario_2_multi_turn_conversation`
- **验证内容**:
  - 第一轮：完整占卜请求，获得结果和 session_id
  - 第二轮：使用 session_id 发送追问
  - 验证上下文连续性（第二轮能够关联第一轮的主题）
  - session_id 在多轮对话中保持一致

### 场景 3：RAG 增强对比

- **测试函数**: `test_scenario_3_rag_enhancement_comparison`
- **验证内容**:
  - 对同一问题，分别使用禁用和启用 RAG 的 Agent
  - 对比两个回复的质量差异
  - 统计知识关键词出现频率
  - 验证 RAG 增强的有效性

### 附加测试

#### 性能基准测试
- **测试函数**: `test_scenario_performance_benchmark`
- **验证内容**:
  - 完整占卜流程在 30 秒内完成
  - 记录实际处理时间

#### 错误处理测试
- **测试函数**: `test_scenario_error_handling_invalid_numbers`
- **验证内容**:
  - 无效的报数（超出 1-6 范围）
  - 系统优雅地处理并返回错误提示

## 运行测试

### 前置条件

1. **数据库准备**
   ```bash
   # 确保数据库已启动并初始化
   ./scripts/init_db.sh
   ```

2. **环境变量配置**
   ```bash
   # 必需的环境变量
   export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
   export OPENAI_API_KEY="sk-..."
   
   # 可选的环境变量
   export LLM_MODEL="gpt-4o-mini"
   export EMBEDDING_MODEL="text-embedding-3-small"
   ```

3. **知识库数据加载**
   ```bash
   # 确保知识库数据已加载（至少 6 条六宫记录）
   python scripts/load_kb_from_markdown.py
   ```

### 运行所有 E2E 测试

```bash
# 运行所有端到端测试
pytest tests/e2e/test_full_divination_flow.py -v

# 运行特定场景
pytest tests/e2e/test_full_divination_flow.py::test_scenario_1_first_time_divination_complete_slots -v

# 运行并显示详细输出
pytest tests/e2e/test_full_divination_flow.py -v -s
```

### 运行标记的测试

```bash
# 只运行 E2E 测试
pytest -m e2e -v

# 跳过慢速测试
pytest -m "e2e and not slow" -v
```

## 部署验证

在部署到生产环境之前，运行部署验证脚本：

```bash
# 运行部署验证脚本
python scripts/verify_deployment.py

# 或直接执行
./scripts/verify_deployment.py
```

### 验证检查项

部署验证脚本会检查以下内容：

1. **环境变量验证**
   - DATABASE_URL（必需）
   - OPENAI_API_KEY（必需）
   - REDIS_URL（可选）
   - EMBEDDING_MODEL（可选）
   - LLM_MODEL（可选）

2. **数据库连接验证**
   - PostgreSQL 连接
   - pgvector 扩展安装状态

3. **数据库表结构验证**
   - users, user_profiles
   - divination_records
   - gongs, shous, qins, dizhis

4. **知识库数据验证**
   - 六宫数据（至少 6 条）
   - 六兽数据（至少 6 条）
   - 六亲数据（至少 5 条）
   - 地支数据（至少 12 条）

5. **OpenAI API 验证**
   - LLM 模型可用性
   - Embedding 模型可用性

6. **应用程序启动验证**
   - FastAPI 应用初始化
   - 必要路由注册

### 验证结果

脚本会输出每个检查项的结果，并在最后显示总结：

```
============================================================
  验证总结
============================================================

总检查项: 15
✓ 通过: 15
✗ 失败: 0
成功率: 100.0%

✓ 所有检查通过！系统部署完整。
```

## 测试数据清理

所有测试使用 pytest fixture 的 teardown 机制自动清理：

- **测试用户**: 测试结束后自动删除
- **占卜记录**: 级联删除（通过外键约束）
- **数据库事务**: 测试结束后回滚（`db_session` fixture）

不需要手动清理测试数据。

## CI/CD 集成

在 CI/CD 管道中运行测试：

```yaml
# GitHub Actions 示例
- name: Run E2E Tests
  run: |
    pytest tests/e2e/test_full_divination_flow.py -v --tb=short
  env:
    DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## 故障排查

### 常见问题

1. **数据库连接失败**
   ```
   错误: FATAL:  database "xxx" does not exist
   解决: 运行 ./scripts/init_db.sh 初始化数据库
   ```

2. **知识库数据不足**
   ```
   错误: 仅有 0 条六宫记录（至少需要 6 条）
   解决: 运行 python scripts/load_kb_from_markdown.py 加载数据
   ```

3. **OpenAI API 失败**
   ```
   错误: Incorrect API key provided
   解决: 检查 OPENAI_API_KEY 环境变量是否正确设置
   ```

4. **测试超时**
   ```
   错误: Timeout waiting for response
   解决: 
   - 检查网络连接
   - 增加超时时间（修改 tool_timeout 参数）
   - 使用更快的模型（如 gpt-4o-mini）
   ```

## 性能建议

- **并行测试**: 使用 `pytest-xdist` 插件并行运行测试
  ```bash
  pytest -n auto tests/e2e/
  ```

- **跳过慢速测试**: 在快速验证时跳过标记为 `slow` 的测试
  ```bash
  pytest -m "not slow" tests/e2e/
  ```

- **使用本地缓存**: 考虑缓存 Embedding 结果以加快测试速度

## 注意事项

1. **真实数据库**: 测试使用真实数据库连接，不使用 Mock
2. **API 调用**: 测试会实际调用 OpenAI API，产生费用
3. **测试隔离**: 每个测试使用独立的用户和会话，确保测试隔离
4. **幂等性**: 测试可以重复运行，不会产生副作用

## 联系支持

如有问题，请查看：
- 项目文档: `/docs`
- 架构说明: `/ARCHITECTURE.md`
- 变更日志: `/openspec/changes`
