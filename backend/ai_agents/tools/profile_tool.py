"""用户画像工具
提供给 Agent 调用的用户信息查询功能
"""

from typing import Dict, Any, Optional
import logging

from ..services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class ProfileTool:
    """用户画像工具类"""
    
    def __init__(self, memory_service: MemoryService):
        """
        初始化用户画像工具
        
        Args:
            memory_service: 记忆服务实例
        """
        self.memory_service = memory_service
    
    def get_profile(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户画像
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户画像字典
        """
        logger.info("Getting profile for user_id: %d", user_id)
        
        try:
            # 查询用户画像
            profile = self.memory_service.get_user_profile(user_id)
            
            if profile is None:
                # 用户不存在，创建默认画像
                logger.warning("User profile not found for user_id: %d, returning default", user_id)
                return {
                    "success": True,
                    "profile": {
                        "user_id": user_id,
                        "gender": None,
                        "total_divinations": 0,
                        "total_conversations": 0,
                        "preferred_question_types": None
                    },
                    "exists": False
                }
            
            return {
                "success": True,
                "profile": profile,
                "exists": True
            }
            
        except Exception as e:
            logger.error("Failed to get user profile: %s", e)
            return {
                "success": False,
                "profile": None,
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
                "name": "get_user_profile",
                "description": "获取用户画像信息，包括性别、历史占卜次数、偏好问题类型等。用于个性化解释生成。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "用户 ID"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        }
