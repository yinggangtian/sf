"""共享的 pytest fixtures"""

from typing import Generator
import importlib

pytest = importlib.import_module("pytest")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime

from backend.shared.config.settings import get_settings
from backend.shared.db.models.user import User, UserProfile
from backend.shared.db.models.divination import DivinationRecord


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


@pytest.fixture(name="test_user", scope="function")
def test_user_fixture(db_session: Session) -> Generator[User, None, None]:
    """
    创建测试用户
    
    测试结束后自动清理
    """
    # 创建测试用户
    user = User(
        username=f"test_user_{datetime.now().timestamp()}",
        email=f"test_{datetime.now().timestamp()}@example.com",
        password_hash="hashed_password_for_testing",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # 创建用户画像
    profile = UserProfile(
        user_id=user.id,
        gender="男",
        location="北京"
    )
    db_session.add(profile)
    db_session.commit()
    
    yield user
    
    # 清理：删除测试用户（级联删除相关记录）
    db_session.query(DivinationRecord).filter(DivinationRecord.user_id == user.id).delete()
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.query(User).filter(User.id == user.id).delete()
    db_session.commit()


@pytest.fixture(name="seed_knowledge_base", scope="session")
def seed_knowledge_base_fixture() -> Generator[None, None, None]:
    """
    在测试会话开始时确保知识库数据已加载
    
    验证至少有 6 条六宫相关记录
    """
    # TODO: 实际实现应该检查知识库表并插入必要的数据
    # 当前假设知识库已通过脚本预加载
    yield
    # 会话结束后不清理知识库数据（知识库是共享资源）
