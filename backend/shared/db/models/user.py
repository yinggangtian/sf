"""
用户相关数据模型 - ORM Models
包含用户基本信息、用户画像等表定义
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(100), nullable=False, unique=True, index=True, comment="用户名")
    email = Column(String(255), nullable=True, unique=True, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="账号是否激活")
    is_verified = Column(Boolean, default=False, comment="邮箱是否验证")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    
    # 关系
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    divination_records = relationship("DivinationRecord", back_populates="user", cascade="all, delete-orphan")
    conversation_summaries = relationship("ConversationSummary", back_populates="user", cascade="all, delete-orphan")
    find_object_records = relationship("FindObjectRecord", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class UserProfile(Base):
    """用户画像表"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True, comment="画像ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True, comment="用户ID")
    
    # 基本信息
    gender = Column(String(10), nullable=True, comment="性别")
    birth_date = Column(DateTime(timezone=True), nullable=True, comment="出生日期")
    location = Column(String(200), nullable=True, comment="所在地")
    
    # 偏好设置
    preferred_question_types = Column(Text, nullable=True, comment="常问问题类型(JSON数组)")
    notification_enabled = Column(Boolean, default=True, comment="是否启用通知")
    
    # 统计信息
    total_divinations = Column(Integer, default=0, comment="总占卜次数")
    total_conversations = Column(Integer, default=0, comment="总对话次数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, gender={self.gender})>"
