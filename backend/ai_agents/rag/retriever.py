"""检索器
使用 pgvector 进行向量相似度检索
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .embedder import Embedder
from .schemas import SearchResult


class Retriever:
    """向量检索器（使用 pgvector）"""
    
    def __init__(self, embedder: Optional[Embedder] = None):
        """
        初始化检索器
        
        Args:
            embedder: 嵌入生成器（可选，默认创建新实例）
        """
        self.embedder = embedder or Embedder()
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        db_session: Optional[Session] = None
    ) -> List[SearchResult]:
        """
        执行向量检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            db_session: 数据库会话（如果需要从数据库检索）
            
        Returns:
            检索结果列表
            
        Note:
            当前实现返回模拟数据，实际应从 pgvector 数据库检索
        """
        # 生成查询向量
        try:
            query_embedding = self.embedder.embed_text(query)
        except Exception:
            # 嵌入失败时返回空结果
            return []
        
        # TODO: 实际实现应该：
        # 1. 使用 query_embedding 在 pgvector 表中查询
        # 2. 按相似度排序
        # 3. 返回 top_k 个结果
        
        # 当前返回模拟数据用于测试
        mock_results = [
            SearchResult(
                chunk_text="大安宫位主安定吉祥，五行属木，代表稳固和成长。",
                metadata={"source": "小六壬经典", "chapter": "六宫详解"},
                score=0.95
            ),
            SearchResult(
                chunk_text="留连宫位主事情拖延，需要耐心等待时机。",
                metadata={"source": "小六壬经典", "chapter": "六宫详解"},
                score=0.88
            ),
            SearchResult(
                chunk_text="速喜宫位主喜事将至，宜把握机会行动。",
                metadata={"source": "小六壬经典", "chapter": "六宫详解"},
                score=0.82
            ),
        ]
        
        # 按 score 降序排列
        mock_results.sort(key=lambda x: x.score, reverse=True)
        
        return mock_results[:top_k]
    
    def batch_search(
        self,
        queries: List[str],
        top_k: int = 5,
        db_session: Optional[Session] = None
    ) -> Dict[str, List[SearchResult]]:
        """
        批量检索
        
        Args:
            queries: 查询文本列表
            top_k: 每个查询返回的结果数量
            db_session: 数据库会话
            
        Returns:
            查询文本到结果列表的映射
        """
        results = {}
        for query in queries:
            results[query] = self.search(query, top_k, db_session)
        return results
