"""记忆服务层
负责用户画像和对话摘要的读写管理
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.shared.db.models.user import User, UserProfile
from backend.shared.db.models.divination import ConversationSummary


class MemoryService:
    """记忆管理服务类"""
    
    def __init__(self, db_session: Session):
        """
        初始化记忆服务
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        查询用户画像
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户画像字典，如果不存在返回 None
        """
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            return None
        
        return {
            "user_id": profile.user_id,
            "gender": profile.gender,
            "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
            "location": profile.location,
            "preferred_question_types": profile.preferred_question_types,
            "notification_enabled": profile.notification_enabled,
            "total_divinations": profile.total_divinations,
            "total_conversations": profile.total_conversations,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        }
    
    def update_profile(
        self,
        user_id: int,
        gender: Optional[str] = None,
        birth_date: Optional[datetime] = None,
        location: Optional[str] = None,
        preferred_question_types: Optional[str] = None,
        notification_enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        更新用户画像（不存在时自动创建）
        
        Args:
            user_id: 用户 ID
            gender: 性别
            birth_date: 出生日期
            location: 所在地
            preferred_question_types: 常问问题类型（JSON数组字符串）
            notification_enabled: 是否启用通知
            
        Returns:
            更新后的用户画像字典
        """
        # 查询现有画像
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        # 不存在则创建
        if not profile:
            # 先检查用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"用户 ID {user_id} 不存在")
            
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        # 更新字段（仅更新非 None 的值）
        if gender is not None:
            profile.gender = gender
        if birth_date is not None:
            profile.birth_date = birth_date
        if location is not None:
            profile.location = location
        if preferred_question_types is not None:
            profile.preferred_question_types = preferred_question_types
        if notification_enabled is not None:
            profile.notification_enabled = notification_enabled
        
        self.db.commit()
        self.db.refresh(profile)
        
        return self.get_user_profile(user_id)
    
    def increment_divination_count(self, user_id: int) -> None:
        """
        增加用户占卜次数统计
        
        Args:
            user_id: 用户 ID
        """
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if profile:
            profile.total_divinations += 1
            self.db.commit()
    
    def increment_conversation_count(self, user_id: int) -> None:
        """
        增加用户对话次数统计
        
        Args:
            user_id: 用户 ID
        """
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if profile:
            profile.total_conversations += 1
            self.db.commit()
    
    def get_conversation_summary(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户最新的对话摘要
        
        Args:
            user_id: 用户 ID
            
        Returns:
            对话摘要字典，如果不存在返回 None
        """
        summary = self.db.query(ConversationSummary).filter(
            ConversationSummary.user_id == user_id
        ).order_by(ConversationSummary.end_time.desc()).first()
        
        if not summary:
            return None
        
        return {
            "id": summary.id,
            "user_id": summary.user_id,
            "summary_text": summary.summary_text,
            "keywords": summary.keywords,
            "total_messages": summary.total_messages,
            "divination_count": summary.divination_count,
            "start_time": summary.start_time.isoformat() if summary.start_time else None,
            "end_time": summary.end_time.isoformat() if summary.end_time else None,
            "created_at": summary.created_at.isoformat() if summary.created_at else None,
            "updated_at": summary.updated_at.isoformat() if summary.updated_at else None
        }
    
    def update_summary(
        self,
        user_id: int,
        summary_text: str,
        keywords: Optional[List[str]] = None,
        increment_messages: int = 1,
        increment_divinations: int = 0
    ) -> Dict[str, Any]:
        """
        更新对话摘要（追加新轮对话）
        
        如果摘要文本超过 1000 字符，会触发压缩（当前实现为截断，未来可集成 LLM 压缩）
        
        Args:
            user_id: 用户 ID
            summary_text: 新的摘要文本（会追加到现有摘要）
            keywords: 关键词列表
            increment_messages: 增加的消息数（默认 1）
            increment_divinations: 增加的占卜次数（默认 0）
            
        Returns:
            更新后的对话摘要字典
        """
        # 查询最新的摘要
        summary = self.db.query(ConversationSummary).filter(
            ConversationSummary.user_id == user_id
        ).order_by(ConversationSummary.end_time.desc()).first()
        
        current_time = datetime.now()
        
        if not summary:
            # 创建新摘要
            summary = ConversationSummary(
                user_id=user_id,
                summary_text=summary_text,
                keywords=keywords,
                total_messages=increment_messages,
                divination_count=increment_divinations,
                start_time=current_time,
                end_time=current_time
            )
            self.db.add(summary)
        else:
            # 追加摘要文本
            combined_text = f"{summary.summary_text}\n{summary_text}"
            
            # 触发压缩（简单截断策略，保留最后 1000 字符）
            if len(combined_text) > 1000:
                combined_text = "...(历史摘要已压缩)\n" + combined_text[-900:]
            
            summary.summary_text = combined_text
            summary.keywords = keywords or summary.keywords
            summary.total_messages += increment_messages
            summary.divination_count += increment_divinations
            summary.end_time = current_time
        
        self.db.commit()
        self.db.refresh(summary)
        
        return self.get_conversation_summary(user_id)
    
    def get_all_summaries(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取用户的所有对话摘要（按时间倒序）
        
        Args:
            user_id: 用户 ID
            limit: 返回数量限制
            
        Returns:
            对话摘要列表
        """
        summaries = self.db.query(ConversationSummary).filter(
            ConversationSummary.user_id == user_id
        ).order_by(ConversationSummary.end_time.desc()).limit(limit).all()
        
        return [
            {
                "id": s.id,
                "user_id": s.user_id,
                "summary_text": s.summary_text,
                "keywords": s.keywords,
                "total_messages": s.total_messages,
                "divination_count": s.divination_count,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None
            }
            for s in summaries
        ]
