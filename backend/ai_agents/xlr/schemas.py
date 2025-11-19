"""
XLR 数据传输对象 (DTOs)
API 输入输出模型，使用 Pydantic 进行数据验证
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==================== 起卦相关 ====================

class QiguaRequest(BaseModel):
    """起卦请求模型"""
    number1: int = Field(..., ge=1, le=6, description="第一个报数(1-6)")
    number2: int = Field(..., ge=1, le=6, description="第二个报数(1-6)")
    qigua_time: datetime = Field(..., description="起卦时间")
    question_type: Optional[str] = Field(None, description="问题类型")
    gender: Optional[str] = Field(None, description="性别")
    user_id: Optional[int] = Field(None, description="用户ID")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class QiguaInfo(BaseModel):
    """起卦信息模型"""
    number1: int = Field(..., description="第一个报数")
    number2: int = Field(..., description="第二个报数")
    qigua_time: datetime = Field(..., description="起卦时间")
    luogong: int = Field(..., ge=1, le=6, description="落宫位置(1-6)")
    shichen_info: Dict[str, Any] = Field(..., description="时辰信息")
    ti_gong: Optional[int] = Field(None, ge=1, le=6, description="体宫位置（第一个数，主位）")
    yong_gong: Optional[int] = Field(None, ge=1, le=6, description="用宫位置（第二个数，客位）")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class PaipanResult(BaseModel):
    """排盘结果模型"""
    qigua_info: QiguaInfo = Field(..., description="起卦信息")
    paipan_data: Dict[str, Any] = Field(..., description="完整排盘数据")
    creation_time: datetime = Field(default_factory=datetime.now, description="生成时间")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


# ==================== 解卦相关 ====================

class JieguaRequest(BaseModel):
    """解卦请求模型"""
    paipan_result: PaipanResult = Field(..., description="排盘结果")
    question_type: str = Field(..., description="问题类型")
    gender: str = Field(..., description="性别")
    user_id: Optional[int] = Field(None, description="用户ID")


class InterpretationResult(BaseModel):
    """解卦结果模型"""
    yongshen: List[str] = Field(..., description="用神列表")
    gong_analysis: Dict[str, Any] = Field(..., description="宫位分析")
    comprehensive_interpretation: str = Field(..., description="综合解读文本")
    detailed_analysis: Dict[str, Any] = Field(..., description="详细分析数据")


# ==================== 寻物专项 ====================

class FindObjectRequest(BaseModel):
    """寻物请求模型"""
    paipan_result: PaipanResult = Field(..., description="排盘结果")
    item_description: str = Field(..., max_length=200, description="物品描述")
    user_id: Optional[int] = Field(None, description="用户ID")


class FindObjectResult(BaseModel):
    """寻物结果模型"""
    direction_analysis: Dict[str, Any] = Field(..., description="方位分析")
    location_clues: List[str] = Field(..., description="位置线索列表")
    time_estimation: Dict[str, Any] = Field(..., description="时间估计")
    success_probability: float = Field(..., ge=0.0, le=1.0, description="找到概率(0-1)")
    detailed_guidance: str = Field(..., description="详细指导")


# ==================== 历史记录 ====================

class HistoryQueryParams(BaseModel):
    """历史查询参数"""
    user_id: int = Field(..., description="用户ID")
    limit: int = Field(10, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")
    question_type: Optional[str] = Field(None, description="问题类型筛选")


class HistoryResponse(BaseModel):
    """历史记录响应模型"""
    records: List[Dict[str, Any]] = Field(..., description="占卜记录列表")
    total_count: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="页大小")


# ==================== 统一 API 响应 ====================

class ApiResponse(BaseModel):
    """统一API响应模型"""
    success: bool = Field(True, description="请求是否成功")
    data: Optional[Any] = Field(None, description="响应数据")
    message: str = Field("Success", description="响应消息")
    error_code: Optional[str] = Field(None, description="错误代码")


# ==================== 知识库数据 Schemas ====================

class GongSchema(BaseModel):
    """六宫数据 Schema"""
    id: int
    name: str
    position: int
    wuxing: str
    meaning: str
    attributes: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ShouSchema(BaseModel):
    """六兽数据 Schema"""
    id: int
    name: str
    position: int
    wuxing: str
    characteristics: str
    meaning: str
    attributes: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class QinSchema(BaseModel):
    """六亲数据 Schema"""
    id: int
    name: str
    relationship: str
    meaning: str
    usage_context: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class DiZhiSchema(BaseModel):
    """地支数据 Schema"""
    id: int
    name: str
    order: int
    wuxing: str
    shichen: str
    meaning: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
