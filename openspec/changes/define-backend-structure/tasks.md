## 1. 文档与规范
- [ ] 1.1 创建 `ARCHITECTURE.md` 描述三层架构与模块职责
- [ ] 1.2 更新 `openspec/project.md` 补充架构模式说明
- [ ] 1.3 在 `README.md` 中引用 `ARCHITECTURE.md`

## 2. 目录骨架（不含实现）
- [ ] 2.1 创建 `app/routes/` 骨架（health, ai, auth, user, admin）
- [ ] 2.2 创建 `backend/ai_agents/` 目录结构（agents, tools, xlr, rag, prompts）
- [ ] 2.3 创建 `backend/normal_backend/` 目录结构（auth, user, payment, notification）
- [ ] 2.4 创建 `backend/shared/db/` 统一数据层

## 3. 接口约定
- [ ] 3.1 定义 `backend/shared/db/base.py` 与 `session.py` 接口
- [ ] 3.2 定义 `app/dependencies.py` 注入规范（get_db, get_agent, get_current_user）
- [ ] 3.3 定义异常类层次（`backend/shared/exceptions.py`）

## 4. 测试结构
- [ ] 4.1 创建 `tests/test_ai_agents/`, `tests/test_normal_backend/`, `tests/test_integration/` 目录
- [ ] 4.2 添加空的测试骨架文件
