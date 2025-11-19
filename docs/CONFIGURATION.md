# 配置文件使用说明

## 快速开始

### 1. 创建环境配置文件

```bash
cp .env.example .env
```

### 2. 编辑 .env 文件

**必须修改的配置项**：

```bash
# 数据库密码
DB_PASSWORD=your_actual_password

# OpenAI API Key
OPENAI_API_KEY=sk-your-actual-api-key-here

# JWT 密钥（生产环境必须修改）
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

**可选修改的配置项**：

```bash
# 数据库配置（如果使用非默认设置）
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=xiaoliuren
DB_USER=postgres

# Redis 配置（如果有密码）
REDIS_PASSWORD=your_redis_password

# OpenAI 模型配置
OPENAI_MODEL=gpt-4o  # 或 gpt-4o-mini
OPENAI_TEMPERATURE=0.7
```

### 3. 验证配置

运行验证脚本确保所有配置正确加载：

```bash
uv run python scripts/verify_config.py
```

**预期输出**：
- ✅ 配置模块导入成功
- ✅ 所有配置项已正确加载
- ⚠️ 可能的警告（如未设置 OPENAI_API_KEY）

## 配置说明

### 应用配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `APP_NAME` | 应用名称 | 玄学大师AI Agent |
| `ENVIRONMENT` | 运行环境 (development/production/test) | development |
| `DEBUG` | 调试模式 | true |

### 数据库配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DB_HOST` | PostgreSQL 主机地址 | localhost |
| `DB_PORT` | PostgreSQL 端口 | 5432 |
| `DB_NAME` | 数据库名称 | xiaoliuren |
| `DB_USER` | 数据库用户 | postgres |
| `DB_PASSWORD` | 数据库密码 | **必须设置** |
| `DB_POOL_SIZE` | 连接池大小 | 10 |
| `DB_MAX_OVERFLOW` | 连接池最大溢出 | 20 |
| `DB_ECHO` | 是否输出 SQL 日志 | false |

### Redis 缓存配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `REDIS_HOST` | Redis 主机地址 | localhost |
| `REDIS_PORT` | Redis 端口 | 6379 |
| `REDIS_DB` | Redis 数据库编号 | 0 |
| `REDIS_PASSWORD` | Redis 密码（可选） | (空) |
| `ENABLE_CACHE` | 是否启用缓存 | true |
| `KB_CACHE_TTL` | 知识库缓存时间（秒） | 3600 |
| `USER_CACHE_TTL` | 用户会话缓存时间（秒） | 1800 |

### OpenAI 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | **必须设置** |
| `OPENAI_MODEL` | 使用的模型 | gpt-4o |
| `OPENAI_TEMPERATURE` | 温度参数 (0-1) | 0.7 |
| `OPENAI_TIMEOUT` | 请求超时（秒） | 30 |

### RAG 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `EMBEDDING_MODEL` | 向量化模型 | text-embedding-3-large |
| `RAG_TOP_K` | 检索 Top-K 结果数 | 5 |
| `RAG_SCORE_THRESHOLD` | 相似度阈值 | 0.7 |
| `RAG_TIMEOUT` | 检索超时（秒） | 10 |

### JWT 认证配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `JWT_SECRET_KEY` | JWT 签名密钥 | **生产环境必须修改** |
| `JWT_ALGORITHM` | JWT 算法 | HS256 |
| `JWT_EXPIRE_MINUTES` | Token 过期时间（分钟） | 1440 (24小时) |

### 业务配置（XLR 算法）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `VALID_NUMBERS` | 有效报数范围 | [1,2,3,4,5,6] |
| `VALID_QUESTION_TYPES` | 有效问题类型 | ["事业","财运","感情",...] |
| `VALID_GENDERS` | 有效性别 | ["男","女"] |
| `DEFAULT_QUESTION_TYPE` | 默认问题类型 | 通用 |
| `MAX_ITEM_DESCRIPTION_LENGTH` | 寻物描述最大长度 | 200 |
| `MAX_RECORDS_PER_USER` | 用户最大记录数 | 1000 |

### 日志配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 (DEBUG/INFO/WARNING/ERROR) | INFO |
| `LOG_FORMAT` | 日志格式 (json/text) | json |
| `LOG_FILE` | 日志文件路径（可选） | (空，仅控制台) |
| `ENABLE_LOGGING` | 是否启用日志 | true |

### 监控配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ENABLE_METRICS` | 是否启用指标采集 | false |
| `ENABLE_TRACING` | 是否启用链路追踪 | false |

## 环境特定配置

### 开发环境 (development)

```bash
ENVIRONMENT=development
DEBUG=true
DB_ECHO=true  # 可选：查看 SQL 日志
LOG_LEVEL=DEBUG
```

### 生产环境 (production)

```bash
ENVIRONMENT=production
DEBUG=false
DB_ECHO=false

# 生产环境必须设置强密码
DB_PASSWORD=<strong_password>
JWT_SECRET_KEY=<random_hex_64_chars>
OPENAI_API_KEY=<your_api_key>

# 生产环境建议启用监控
ENABLE_METRICS=true
ENABLE_TRACING=true
```

### 测试环境 (test)

```bash
ENVIRONMENT=test
DEBUG=true
DB_NAME=xiaoliuren_test
LOG_LEVEL=WARNING
ENABLE_CACHE=false  # 测试时禁用缓存
```

## 常见问题

### 1. 配置验证失败

**问题**：运行 `verify_config.py` 报错

**解决方案**：
```bash
# 1. 确保已安装依赖
uv sync

# 2. 确保 .env 文件存在
cp .env.example .env

# 3. 检查 .env 文件格式
# 确保没有多余空格，JSON 数组格式正确
```

### 2. 数据库连接失败

**问题**：`database connection failed`

**解决方案**：
```bash
# 1. 检查 PostgreSQL 服务是否运行
# macOS:
brew services list | grep postgresql

# 2. 检查数据库是否存在
psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname='xiaoliuren';"

# 3. 验证密码正确
psql -U postgres -h localhost -d xiaoliuren
```

### 3. OpenAI API Key 无效

**问题**：`OpenAI API authentication failed`

**解决方案**：
```bash
# 1. 验证 API Key 格式（应以 sk- 开头）
echo $OPENAI_API_KEY

# 2. 测试 API Key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### 4. Redis 连接失败

**问题**：`Redis connection refused`

**解决方案**：
```bash
# 1. 检查 Redis 服务是否运行
# macOS:
brew services list | grep redis

# 2. 启动 Redis
brew services start redis

# 3. 测试连接
redis-cli ping
```

## 安全建议

1. **永远不要提交 .env 文件到版本控制**
   - `.env` 已在 `.gitignore` 中

2. **生产环境使用强密钥**
   ```bash
   # 生成随机 JWT 密钥
   openssl rand -hex 32
   
   # 生成随机数据库密码
   openssl rand -base64 32
   ```

3. **定期轮换密钥**
   - JWT 密钥至少每 90 天轮换一次
   - API Key 发现泄露立即撤销

4. **使用环境变量管理工具**
   - 生产环境考虑使用 AWS Secrets Manager、HashiCorp Vault 等

## 下一步

配置完成后，继续执行：

```bash
# Phase 0.2: 初始化数据库
python scripts/init_database.py

# Phase 1: 运行算法单元测试
pytest backend/ai_agents/xlr/tests/

# Phase 2: 启动开发服务器
uvicorn backend.main:app --reload
```
