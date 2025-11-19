"""FastAPI 应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import ai, health


# 创建 FastAPI 应用
app = FastAPI(
    title="玄学大师 AI Agent API",
    description="基于小六壬算法的 AI 占卜系统",
    version="1.0.0"
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
