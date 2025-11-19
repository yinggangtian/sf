"""
知识库数据模型 - ORM Models
包含六宫、六兽、六亲、地支等玄学知识库表定义
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from ..base import Base


class Gong(Base):
    """六宫数据表"""
    __tablename__ = "liu_gong"
    
    id = Column(Integer, primary_key=True, index=True, comment="宫位ID")
    name = Column(String(50), nullable=False, unique=True, comment="宫位名称")
    position = Column(Integer, nullable=False, unique=True, index=True, comment="位置序号(1-6)")
    wuxing = Column(String(20), nullable=False, comment="五行属性")
    meaning = Column(Text, nullable=False, comment="含义描述")
    attributes = Column(JSON, nullable=True, comment="其他属性(JSON格式)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Gong(name={self.name}, position={self.position}, wuxing={self.wuxing})>"


class Shou(Base):
    """六兽数据表"""
    __tablename__ = "liu_shou"
    
    id = Column(Integer, primary_key=True, index=True, comment="六兽ID")
    name = Column(String(50), nullable=False, unique=True, comment="六兽名称")
    position = Column(Integer, nullable=False, unique=True, index=True, comment="位置序号(1-6)")
    wuxing = Column(String(20), nullable=False, comment="五行属性")
    characteristics = Column(Text, nullable=False, comment="特征描述")
    meaning = Column(Text, nullable=False, comment="含义描述")
    attributes = Column(JSON, nullable=True, comment="其他属性(JSON格式)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Shou(name={self.name}, position={self.position}, wuxing={self.wuxing})>"


class Qin(Base):
    """六亲数据表"""
    __tablename__ = "liu_qin"
    
    id = Column(Integer, primary_key=True, index=True, comment="六亲ID")
    name = Column(String(50), nullable=False, unique=True, comment="六亲名称")
    relationship = Column(String(100), nullable=False, comment="关系类型")
    meaning = Column(Text, nullable=False, comment="含义描述")
    usage_context = Column(Text, nullable=True, comment="使用语境")
    attributes = Column(JSON, nullable=True, comment="其他属性(JSON格式)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Qin(name={self.name}, relationship={self.relationship})>"


class DiZhi(Base):
    """地支数据表"""
    __tablename__ = "di_zhi"
    
    id = Column(Integer, primary_key=True, index=True, comment="地支ID")
    name = Column(String(10), nullable=False, unique=True, comment="地支名称")
    order = Column(Integer, nullable=False, unique=True, index=True, comment="顺序(1-12)")
    wuxing = Column(String(20), nullable=False, comment="五行属性")
    shichen = Column(String(50), nullable=False, comment="对应时辰")
    meaning = Column(Text, nullable=True, comment="含义描述")
    attributes = Column(JSON, nullable=True, comment="其他属性(JSON格式)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<DiZhi(name={self.name}, order={self.order}, wuxing={self.wuxing})>"


class TianGan(Base):
    """天干数据表"""
    __tablename__ = "tian_gan"

    id = Column(Integer, primary_key=True, index=True, comment="天干ID")
    name = Column(String(10), nullable=False, unique=True, comment="天干名称")
    order = Column(Integer, nullable=False, unique=True, index=True, comment="顺序(1-10)")
    wuxing = Column(String(20), nullable=False, comment="五行属性")
    yin_yang = Column(String(10), nullable=False, comment="阴阳属性")
    meaning = Column(Text, nullable=True, comment="含义描述")
    attributes = Column(JSON, nullable=True, comment="其他属性(JSON格式)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<TianGan(name={self.name}, order={self.order}, yin_yang={self.yin_yang})>"


class WuxingRelation(Base):
    """五行关系表"""
    __tablename__ = "wuxing_relations"
    
    id = Column(Integer, primary_key=True, index=True, comment="关系ID")
    element1 = Column(String(20), nullable=False, comment="五行1")
    element2 = Column(String(20), nullable=False, comment="五行2")
    relation = Column(String(20), nullable=False, comment="关系类型(生/克/同/无)")
    description = Column(Text, nullable=True, comment="关系描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<WuxingRelation({self.element1}-{self.relation}-{self.element2})>"


__all__ = [
    "Gong",
    "Shou",
    "Qin",
    "DiZhi",
    "TianGan",
    "WuxingRelation",
]
