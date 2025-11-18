"""
数据库基础配置
SQLAlchemy Base 和基础设置
"""

from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemy Base - 所有 ORM 模型的基类
Base = declarative_base()
