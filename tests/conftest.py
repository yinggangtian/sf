"""共享的 pytest fixtures"""

from typing import Generator
import importlib

pytest = importlib.import_module("pytest")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.shared.config.settings import get_settings


@pytest.fixture(name="db_session", scope="function")
def db_session_fixture() -> Generator[Session, None, None]:
    """
    创建测试数据库会话
    
    每个测试函数使用独立的会话，测试结束后自动回滚
    """
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    
    session = SessionLocal()
    try:
        yield session
        session.rollback()  # 测试结束后回滚，保持数据库干净
    finally:
        session.close()
