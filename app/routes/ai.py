"""AI Agent 相关路由
处理占卜请求、历史查询等

采用 OpenAI Responses API 格式 (POST /v1/responses)
"""

from typing import Optional, Dict, Any, List, Union, Literal, cast
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import uuid
import time

from app.dependencies import get_current_user, get_master_agent
from backend.shared.db.models.user import User
from backend.ai_agents.agents.master_agent import MasterAgent


router = APIRouter(prefix="/v1", tags=["AI Agent"])


# ==================== Request/Response Schemas (OpenAI Responses API 格式) ====================

class ResponseInput(BaseModel):
    """Responses API 输入项（支持多种格式）"""
    type: Literal["message"] = Field("message", description="输入类型")
    role: Literal["user", "assistant", "system"] = Field("user", description="消息角色")
    content: str = Field(..., description="消息内容")


class ResponseRequest(BaseModel):
    """OpenAI Responses API 请求格式
    
    兼容 OpenAI POST /v1/responses 格式
    """
    model: str = Field(default="gpt-4o", description="模型名称")
    input: Union[str, List[ResponseInput]] = Field(..., description="用户输入（字符串或消息数组）")
    instructions: Optional[str] = Field(None, description="系统指令")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    # 扩展字段
    user_id: Optional[int] = Field(None, description="用户 ID")
    session_id: Optional[str] = Field(None, description="会话 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4o",
                "input": "我想算事业运势，报数 3 和 5，男",
                "user_id": 1,
                "session_id": "session-001"
            }
        }


class OutputMessage(BaseModel):
    """输出消息格式"""
    type: Literal["message"] = Field("message", description="输出类型")
    role: Literal["assistant"] = Field("assistant", description="角色")
    content: List[Dict[str, Any]] = Field(..., description="内容列表")


class ResponseUsage(BaseModel):
    """Token 使用统计"""
    input_tokens: int = Field(default=0, description="输入 token 数")
    output_tokens: int = Field(default=0, description="输出 token 数")
    total_tokens: int = Field(default=0, description="总 token 数")


class ResponseOutput(BaseModel):
    """OpenAI Responses API 响应格式"""
    id: str = Field(..., description="响应 ID")
    object: Literal["response"] = Field("response", description="对象类型")
    created_at: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="使用的模型")
    status: Literal["completed", "failed", "in_progress", "incomplete"] = Field(..., description="响应状态")
    output: List[OutputMessage] = Field(..., description="输出消息列表")
    usage: ResponseUsage = Field(default_factory=ResponseUsage, description="Token 使用统计")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    # 扩展字段：占卜特有数据
    divination_result: Optional[Dict[str, Any]] = Field(None, description="占卜结果（结构化）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "resp_abc123",
                "object": "response",
                "created_at": 1699564800,
                "model": "gpt-4o",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "根据您的占卜，此卦落于坎宫..."}
                        ]
                    }
                ],
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "total_tokens": 300
                },
                "divination_result": {
                    "qigua": {"luogong": "坎宫", "yongshen": "青龙"},
                    "jiegua": {"favorable": True}
                }
            }
        }


# ==================== API Endpoints ====================

@router.post("/responses", response_model=ResponseOutput)
async def create_response(
    request: ResponseRequest,
    master_agent: MasterAgent = Depends(get_master_agent),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    OpenAI Responses API 格式 - 执行占卜
    
    兼容 OpenAI 最新推荐的 POST /v1/responses 格式。
    调用 MasterAgent 完成完整的占卜流程：
    1. Orchestrator 意图识别和槽位填充
    2. 调用占卜工具
    3. Explainer 生成解释
    
    Args:
        request: OpenAI Responses API 格式请求
        master_agent: MasterAgent 实例
        current_user: 当前用户（可选）
        
    Returns:
        OpenAI Responses API 格式响应
        
    Raises:
        HTTPException: 400 请求错误、500 服务器错误
    """
    try:
        # 解析输入
        if isinstance(request.input, str):
            user_message = request.input
            conversation_history: List[Dict[str, str]] = []
        else:
            # 从消息数组中提取
            conversation_history = []
            user_message = ""
            for msg in request.input:
                if msg.role == "user":
                    user_message = msg.content  # 取最后一条用户消息
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 确定 user_id
        user_id: int = request.user_id if request.user_id is not None else 0
        if user_id == 0 and current_user is not None:
            user_id = cast(int, current_user.id)
        
        # 调用 MasterAgent
        result = await master_agent.run(
            user_message=user_message,
            user_id=user_id,
            session_id=request.session_id,
            conversation_history=conversation_history
        )
        
        # 转换为 OpenAI Responses API 格式
        response_status = result.get("status", "error")
        api_status: Literal["completed", "failed", "in_progress", "incomplete"]
        if response_status == "success":
            api_status = "completed"
        elif response_status == "clarification_needed":
            api_status = "incomplete"
        else:
            api_status = "failed"
        
        reply_text = result.get("reply", "")
        
        return ResponseOutput(
            id=f"resp_{uuid.uuid4().hex[:12]}",
            object="response",
            created_at=int(time.time()),
            model=request.model,
            status=api_status,
            output=[
                OutputMessage(
                    type="message",
                    role="assistant",
                    content=[{"type": "text", "text": reply_text}]
                )
            ],
            usage=ResponseUsage(
                input_tokens=result.get("meta", {}).get("input_tokens", 0),
                output_tokens=result.get("meta", {}).get("output_tokens", 0),
                total_tokens=result.get("meta", {}).get("total_tokens", 0)
            ),
            metadata={
                "processing_time": result.get("meta", {}).get("processing_time", 0),
                "missing_slots": result.get("missing_slots", []),
                **(request.metadata or {})
            },
            divination_result=result.get("divination_result")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"请求参数错误: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器处理错误: {str(e)}"
        ) from e
