"""数据库会话管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.shared.config.settings import get_settings


# 获取配置
settings = get_settings()

# 创建引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 检查连接有效性
    pool_recycle=3600,   # 1小时回收连接
    echo=False           # 不打印 SQL（生产环境）
)

# 创建会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)


def get_db() -> Session:
    """
    获取数据库会话（不使用 generator）
    
    Returns:
        数据库会话
    """
    return SessionLocal()
