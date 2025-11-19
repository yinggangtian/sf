"""FastAPI 应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import ai, health


# 创建 FastAPI 应用
app = FastAPI(
    title="玄学大师 AI Agent API",
    description="""
## 基于小六壬算法的 AI 占卜系统

### 功能特点
- 🤖 智能对话式占卜流程
- 📊 多种占卜算法支持（小六壬、八字等）
- 🧠 RAG 知识库增强解释
- 📝 完整的占卜历史记录
- 🔐 用户认证与权限管理

### 主要接口
- `/ai/divination` - 执行占卜
- `/ai/history/{user_id}` - 查询历史记录
- `/health` - 健康检查

### 技术栈
- FastAPI + SQLAlchemy
- LangChain + OpenAI
- PostgreSQL + Redis
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "AI Agent",
            "description": "AI 占卜核心功能，包括占卜执行、历史查询等"
        },
        {
            "name": "Health",
            "description": "系统健康检查和状态监控"
        },
        {
            "name": "Auth",
            "description": "用户认证与授权"
        },
        {
            "name": "User",
            "description": "用户管理"
        },
        {
            "name": "Admin",
            "description": "管理员功能"
        }
    ],
    contact={
        "name": "玄学大师团队",
        "email": "support@xuanxue.ai"
    },
    license_info={
        "name": "MIT License"
    }
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router)
app.include_router(ai.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "玄学大师 AI Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }
