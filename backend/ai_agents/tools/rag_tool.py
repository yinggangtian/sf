"""RAG 工具
提供给 Agent 调用的知识库检索功能
"""

from typing import List, Dict, Any
import logging

from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)


class RAGTool:
    """RAG 检索工具类"""
    
    def __init__(self, rag_service: RAGService):
        """
        初始化 RAG 工具
        
        Args:
            rag_service: RAG 服务实例
        """
        self.rag_service = rag_service
    
    def search(
        self,
        keywords: List[str],
        top_k: int = 5,
        timeout: float = 3.0
    ) -> Dict[str, Any]:
        """
        检索知识库
        
        Args:
            keywords: 检索关键词列表
            top_k: 返回结果数量（默认 5）
            timeout: 超时时间（秒，默认 3 秒）
            
        Returns:
            检索结果字典，包含 chunks 和 metadata
        """
        logger.info("RAG search with keywords: %s, top_k: %d", keywords, top_k)
        
        try:
            # 调用 RAG 服务
            response = self.rag_service.search_knowledge(
                keywords=keywords,
                top_k=top_k,
                timeout=timeout
            )
            
            # 转换结果格式
            chunks = []
            for result in response.results:
                chunks.append({
                    "chunk_text": result.chunk_text,
                    "metadata": result.metadata,
                    "score": result.score
                })
            
            return {
                "success": True,
                "chunks": chunks,
                "total_results": len(chunks),
                "degraded": response.degraded
            }
            
        except Exception as e:
            logger.error("RAG search failed: %s", e)
            return {
                "success": False,
                "chunks": [],
                "total_results": 0,
                "error": str(e),
                "degraded": True
            }
    
    @staticmethod
    def get_tool_schema() -> Dict[str, Any]:
        """
        返回工具的 JSON Schema（用于 OpenAI Function Calling）
        
        Returns:
            工具 Schema 字典
        """
        return {
            "type": "function",
            "function": {
                "name": "rag_search",
                "description": "检索六壬知识库，获取相关的典籍内容和解释。支持多关键词检索，返回最相关的知识片段。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "检索关键词列表，例如：['青龙', '坎宫', '用神']"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量，默认 5，范围 1-10",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10
                        },
                        "timeout": {
                            "type": "number",
                            "description": "超时时间（秒），默认 3 秒",
                            "default": 3.0
                        }
                    },
                    "required": ["keywords"]
                }
            }
        }
