"""
数据库会话管理
提供数据库连接和会话创建功能
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from ..config.settings import Settings

# 加载配置
settings = Settings()

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.db_echo,
    pool_pre_ping=True,  # 启用连接健康检查
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    依赖注入函数：获取数据库会话
    用于 FastAPI 的 Depends
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    获取数据库会话（用于脚本和服务）
    注意：使用完毕后需要手动关闭
    """
    return SessionLocal()
