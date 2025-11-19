"""RAG 服务层
负责知识库检索增强，支持超时和降级处理
"""

from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from sqlalchemy.orm import Session

from ..rag.retriever import Retriever
from ..rag.embedder import Embedder
from ..rag.schemas import SearchRequest, SearchResponse, SearchResult


class RAGService:
    """RAG 检索服务类"""
    
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        db_session: Optional[Session] = None
    ):
        """
        初始化 RAG 服务
        
        Args:
            retriever: 检索器实例（可选，默认创建新实例）
            db_session: 数据库会话（可选，用于数据库检索）
        """
        self.retriever = retriever or Retriever()
        self.db_session = db_session
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def search_knowledge(
        self,
        keywords: List[str],
        top_k: int = 5,
        timeout: float = 3.0
    ) -> SearchResponse:
        """
        检索知识库（支持超时）
        
        Args:
            keywords: 检索关键词列表
            top_k: 返回结果数量
            timeout: 超时时间（秒），默认 3 秒
            
        Returns:
            检索响应对象，超时时返回降级结果
        """
        if not keywords:
            return SearchResponse(
                results=[],
                total_count=0,
                degraded=False,
                message="未提供检索关键词"
            )
        
        # 合并关键词为查询文本
        query_text = " ".join(keywords)
        
        try:
            # 使用线程池执行检索，支持超时
            future = self.executor.submit(
                self.retriever.search,
                query_text,
                top_k,
                self.db_session
            )
            
            results = future.result(timeout=timeout)
            
            # 按 score 降序排列（确保顺序）
            results.sort(key=lambda x: x.score, reverse=True)
            
            # 强制限制返回数量为 top_k
            results = results[:top_k]
            
            return SearchResponse(
                results=results,
                total_count=len(results),
                degraded=False,
                message=None
            )
            
        except (FuturesTimeoutError, TimeoutError):
            # 超时降级：返回空结果
            return SearchResponse(
                results=[],
                total_count=0,
                degraded=True,
                message="检索超时，本次未引用典籍片段"
            )
        except Exception as e:
            # 其他异常也降级
            return SearchResponse(
                results=[],
                total_count=0,
                degraded=True,
                message=f"检索失败：{str(e)}"
            )
    
    def batch_search(
        self,
        keyword_groups: List[List[str]],
        top_k: int = 5,
        timeout: float = 3.0
    ) -> Dict[str, SearchResponse]:
        """
        批量检索（支持多关键词组并行）
        
        Args:
            keyword_groups: 关键词组列表
            top_k: 每组返回的结果数量
            timeout: 每个检索的超时时间
            
        Returns:
            关键词组索引到响应的映射
        """
        results = {}
        
        for idx, keywords in enumerate(keyword_groups):
            key = f"group_{idx}"
            results[key] = self.search_knowledge(keywords, top_k, timeout)
        
        return results
    
    def __del__(self):
        """清理线程池"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
