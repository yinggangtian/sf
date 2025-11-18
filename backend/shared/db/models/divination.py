"""
占卜相关数据模型 - ORM Models
包含占卜记录、对话摘要等表定义
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class DivinationRecord(Base):
    """占卜记录表"""
    __tablename__ = "divination_records"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    
    # 起卦数据
    qigua_data = Column(JSON, nullable=False, comment="起卦数据(包含报数、时间、落宫等)")
    
    # 排盘数据
    paipan_data = Column(JSON, nullable=False, comment="排盘数据(包含六宫、六兽排盘)")
    
    # 解卦数据
    interpretation_data = Column(JSON, nullable=True, comment="解卦数据(用神、宫位分析、综合解读)")
    
    # 问题信息
    question_type = Column(String(50), nullable=True, comment="问题类型(事业/财运/感情等)")
    question_desc = Column(Text, nullable=True, comment="问题描述")
    gender = Column(String(10), nullable=True, comment="性别")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="divination_records")
    
    def __repr__(self):
        return f"<DivinationRecord(id={self.id}, user_id={self.user_id}, question_type={self.question_type})>"


class ConversationSummary(Base):
    """对话摘要表"""
    __tablename__ = "conversation_summaries"
    
    id = Column(Integer, primary_key=True, index=True, comment="摘要ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    
    # 摘要内容
    summary_text = Column(Text, nullable=False, comment="摘要文本")
    keywords = Column(JSON, nullable=True, comment="关键词列表")
    
    # 统计信息
    total_messages = Column(Integer, default=0, comment="总消息数")
    divination_count = Column(Integer, default=0, comment="占卜次数")
    
    # 时间范围
    start_time = Column(DateTime(timezone=True), nullable=False, comment="对话开始时间")
    end_time = Column(DateTime(timezone=True), nullable=False, comment="对话结束时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="conversation_summaries")
    
    def __repr__(self):
        return f"<ConversationSummary(id={self.id}, user_id={self.user_id}, total_messages={self.total_messages})>"


class FindObjectRecord(Base):
    """寻物记录表 (专项功能)"""
    __tablename__ = "find_object_records"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    divination_record_id = Column(Integer, ForeignKey("divination_records.id"), nullable=True, comment="关联的占卜记录ID")
    
    # 物品信息
    item_description = Column(Text, nullable=False, comment="物品描述")
    
    # 寻物结果
    direction_analysis = Column(JSON, nullable=False, comment="方位分析结果")
    location_clues = Column(JSON, nullable=False, comment="位置线索列表")
    time_estimation = Column(JSON, nullable=False, comment="时间估计")
    success_probability = Column(Float, nullable=False, comment="找到概率(0-1)")
    detailed_guidance = Column(Text, nullable=False, comment="详细指导")
    
    # 反馈
    found_status = Column(String(20), nullable=True, comment="是否找到(found/not_found/unknown)")
    feedback = Column(Text, nullable=True, comment="用户反馈")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="find_object_records")
    divination_record = relationship("DivinationRecord")
    
    def __repr__(self):
        return f"<FindObjectRecord(id={self.id}, user_id={self.user_id}, found_status={self.found_status})>"
