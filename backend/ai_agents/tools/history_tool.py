"""历史记录工具
提供给 Agent 调用的占卜历史查询功能
"""

from typing import Dict, Any, Optional
import logging

from ..services.divination_service import DivinationService

logger = logging.getLogger(__name__)


class HistoryTool:
    """历史记录工具类"""
    
    def __init__(self, divination_service: DivinationService):
        """
        初始化历史记录工具
        
        Args:
            divination_service: 占卜服务实例
        """
        self.divination_service = divination_service
    
    def get_history(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        question_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户占卜历史统计
        
        Args:
            user_id: 用户 ID
            limit: 保留参数（向后兼容）
            offset: 保留参数（向后兼容）
            question_type: 筛选问题类型（可选）
            
        Returns:
            历史统计字典
        """
        logger.info(
            "Getting history statistics for user_id: %d",
            user_id
        )
        
        try:
            # 查询统计信息（暂时使用统计接口）
            stats = self.divination_service.get_statistics(user_id)
            
            return {
                "success": True,
                "statistics": stats,
                "total_divinations": stats.get("total_divinations", 0),
                "question_types": stats.get("question_type_distribution", {})
            }
            
        except Exception as e:
            logger.error("Failed to get user history: %s", e)
            return {
                "success": False,
                "statistics": {},
                "total_divinations": 0,
                "error": str(e)
            }
    
    def get_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户占卜统计信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            统计信息字典
        """
        logger.info("Getting statistics for user_id: %d", user_id)
        
        try:
            # 查询统计信息
            stats = self.divination_service.get_statistics(user_id)
            
            return {
                "success": True,
                "statistics": {
                    "total_divinations": stats.get("total_divinations", 0),
                    "question_type_distribution": stats.get("question_type_distribution", {}),
                    "favorite_luogong": stats.get("favorite_luogong"),
                    "last_divination_time": stats.get("last_divination_time")
                }
            }
            
        except Exception as e:
            logger.error("Failed to get statistics: %s", e)
            return {
                "success": False,
                "statistics": None,
                "error": str(e)
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
                "name": "get_user_history",
                "description": "获取用户的占卜历史记录，支持分页和按问题类型筛选。用于分析用户的历史占卜模式。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "用户 ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回记录数量，默认 10，最大 50",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "offset": {
                            "type": "integer",
                            "description": "分页偏移量，默认 0",
                            "default": 0,
                            "minimum": 0
                        },
                        "question_type": {
                            "type": "string",
                            "description": "筛选问题类型（可选），例如：'事业'、'财运'、'感情'",
                            "enum": ["事业", "财运", "感情", "健康", "考试", "寻物", "综合"]
                        }
                    },
                    "required": ["user_id"]
                }
            }
        }
