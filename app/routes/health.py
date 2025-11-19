"""健康检查路由"""

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["Health"])


@router.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "service": "玄学大师 AI Agent"
    }
