"""RAG 数据传输对象 (DTOs)
用于知识库检索的请求和响应模型
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """检索请求模型"""
    keywords: List[str] = Field(..., description="检索关键词列表", min_length=1)
    top_k: int = Field(5, ge=1, le=50, description="返回结果数量")
    timeout: float = Field(3.0, gt=0, le=30, description="超时时间（秒）")
    
    
class SearchResult(BaseModel):
    """单个检索结果"""
    chunk_text: str = Field(..., description="文本片段内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据（来源、章节等）")
    score: float = Field(..., ge=0, le=1, description="相似度分数")
    
    
class SearchResponse(BaseModel):
    """检索响应模型"""
    results: List[SearchResult] = Field(default_factory=list, description="检索结果列表")
    total_count: int = Field(0, ge=0, description="结果总数")
    degraded: bool = Field(False, description="是否发生降级（超时或失败）")
    message: Optional[str] = Field(None, description="提示信息")
