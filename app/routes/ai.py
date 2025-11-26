"""AI Agent 相关路由
处理占卜请求、历史查询等
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, get_master_agent, get_divination_service
from backend.shared.db.models.user import User
from backend.ai_agents.agents.master_agent import MasterAgent
from backend.ai_agents.services.divination_service import DivinationService


router = APIRouter(prefix="/ai", tags=["AI Agent"])


# ==================== Request/Response Schemas ====================

class DivinationRequest(BaseModel):
    """占卜请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=1000)
    user_id: int = Field(..., description="用户 ID", gt=0)
    session_id: Optional[str] = Field(None, description="会话 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "我想算事业运势，报数 3 和 5，男",
                "user_id": 1,
                "session_id": "session-001"
            }
        }


class DivinationResponse(BaseModel):
    """占卜响应"""
    reply: str = Field(..., description="AI 回复")
    status: str = Field(..., description="状态：success/clarification_needed/error")
    divination_result: Optional[Dict[str, Any]] = Field(None, description="占卜结果（结构化）")
    meta: Dict[str, Any] = Field(default_factory=dict, description="元信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reply": "根据您的占卜，此卦落于坎宫...",
                "status": "success",
                "divination_result": {
                    "qigua": {"luogong": "坎宫", "yongshen": "青龙"},
                    "jiegua": {"favorable": True}
                },
                "meta": {
                    "processing_time": 2.5,
                    "rag_used": True
                }
            }
        }


class HistoryResponse(BaseModel):
    """历史记录响应"""
    items: list = Field(default_factory=list, description="历史记录列表")
    total: int = Field(..., description="总记录数", ge=0)
    page: int = Field(..., description="当前页码", ge=1)
    page_size: int = Field(..., description="每页大小", ge=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "record_id": 1,
                        "question_type": "事业",
                        "ask_time": "2024-01-15T10:30:00Z",
                        "result_summary": "坎宫青龙..."
                    }
                ],
                "total": 15,
                "page": 1,
                "page_size": 10
            }
        }


# ==================== API Endpoints ====================

@router.post("/divination", response_model=DivinationResponse)
async def create_divination(
    request: DivinationRequest,
    master_agent: MasterAgent = Depends(get_master_agent),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    执行占卜
    
    调用 MasterAgent 完成完整的占卜流程：
    1. Orchestrator 意图识别和槽位填充
    2. 调用占卜工具
    3. Explainer 生成解释
    
    Args:
        request: 占卜请求
        master_agent: MasterAgent 实例
        current_user: 当前用户（可选）
        
    Returns:
        占卜响应
        
    Raises:
        HTTPException: 400 请求错误、500 服务器错误
    """
    try:
        # 调用 MasterAgent
        result = await master_agent.run(
            user_message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            conversation_history=[]  # TODO: 从数据库加载对话历史
        )
        
        # 返回响应
        return DivinationResponse(
            reply=result.get("reply", ""),
            status=result.get("status", "error"),
            divination_result=result.get("divination_result"),
            meta=result.get("meta", {})
        )
        
    except ValueError as e:
        # 参数验证错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"请求参数错误: {str(e)}"
        )
    except Exception as e:
        # 服务器内部错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器处理错误: {str(e)}"
        )


@router.post("/divination/text", response_class=PlainTextResponse)
async def divination_text(
    request: DivinationRequest,
    master_agent: MasterAgent = Depends(get_master_agent),
):
    """
    占卜（纯文本预览）
    
    返回纯 Markdown 文本，方便在 Swagger UI 里阅读调试。
    适合开发时查看 prompt 效果。
    
    Args:
        request: 占卜请求
        master_agent: MasterAgent 实例
        
    Returns:
        纯文本格式的占卜结果（Markdown）
    """
    try:
        # 调用 MasterAgent
        result = await master_agent.run(
            user_message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            conversation_history=[]
        )
        
        reply = result.get("reply", "")
        status_text = result.get("status", "error")
        meta = result.get("meta", {})
        processing_time = meta.get("processing_time", 0)
        
        # 构建纯文本响应
        text_response = f"""{'='*60}
🔮 占卜结果
{'='*60}

📝 请求: {request.message}
👤 用户ID: {request.user_id}
📊 状态: {status_text}
⏱️  处理时间: {processing_time:.2f}秒

{'='*60}

{reply}

{'='*60}
"""
        return text_response
        
    except Exception as e:
        error_text = f"""{'='*60}
❌ 占卜失败
{'='*60}

错误信息: {str(e)}

{'='*60}
"""
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_text
        )


@router.get("/history/{user_id}", response_model=HistoryResponse)
async def get_user_history(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    divination_service: DivinationService = Depends(get_divination_service),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户占卜历史
    
    Args:
        user_id: 用户 ID
        page: 页码（从 1 开始）
        page_size: 每页大小（1-50）
        divination_service: 占卜服务实例
        current_user: 当前用户（可选）
        db: 数据库会话
        
    Returns:
        历史记录响应
        
    Raises:
        HTTPException: 400 请求错误、404 用户不存在、500 服务器错误
    """
    # 参数验证
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="页码必须大于等于 1"
        )
    
    if page_size < 1 or page_size > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="每页大小必须在 1-50 之间"
        )
    
    try:
        # 查询统计信息（暂时使用 statistics 代替完整历史）
        stats = divination_service.get_statistics(user_id)
        
        # 构建响应
        # TODO: 实现真实的历史记录查询
        return HistoryResponse(
            items=[],  # 暂时返回空列表
            total=stats.get("total_divinations", 0),
            page=page,
            page_size=page_size
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器处理错误: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "service": "AI Agent API"
    }
