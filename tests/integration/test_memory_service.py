"""记忆服务集成测试"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from backend.ai_agents.services.memory_service import MemoryService
from backend.shared.db.models.user import User, UserProfile
from backend.shared.db.models.divination import ConversationSummary


@pytest.fixture
def memory_service(db_session: Session) -> MemoryService:
    """创建 MemoryService 实例"""
    return MemoryService(db_session=db_session)


@pytest.fixture
def test_user(db_session: Session) -> User:
    """创建测试用户"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"memory_test_user_{unique_id}",
        email=f"memory_test_{unique_id}@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_get_user_profile_not_exists(memory_service: MemoryService) -> None:
    """测试获取不存在的用户画像"""
    profile = memory_service.get_user_profile(user_id=99999)
    assert profile is None


def test_create_user_profile(memory_service: MemoryService, test_user: User) -> None:
    """测试创建用户画像"""
    profile = memory_service.update_profile(
        user_id=test_user.id,
        gender="男",
        location="北京",
        notification_enabled=True
    )
    
    assert profile is not None
    assert profile["user_id"] == test_user.id
    assert profile["gender"] == "男"
    assert profile["location"] == "北京"
    assert profile["notification_enabled"] is True
    assert profile["total_divinations"] == 0
    assert profile["total_conversations"] == 0


def test_update_existing_profile(memory_service: MemoryService, test_user: User) -> None:
    """测试更新现有用户画像"""
    # 先创建画像
    memory_service.update_profile(
        user_id=test_user.id,
        gender="男",
        location="上海"
    )
    
    # 再更新部分字段
    updated_profile = memory_service.update_profile(
        user_id=test_user.id,
        location="深圳",
        preferred_question_types='["事业", "财运"]'
    )
    
    assert updated_profile["gender"] == "男"  # 保持不变
    assert updated_profile["location"] == "深圳"  # 已更新
    assert updated_profile["preferred_question_types"] == '["事业", "财运"]'


def test_get_user_profile_after_create(memory_service: MemoryService, test_user: User) -> None:
    """测试创建后查询用户画像"""
    memory_service.update_profile(
        user_id=test_user.id,
        gender="女",
        birth_date=datetime(1990, 5, 15)
    )
    
    profile = memory_service.get_user_profile(user_id=test_user.id)
    
    assert profile is not None
    assert profile["gender"] == "女"
    assert profile["birth_date"] is not None
    assert "1990-05-15" in profile["birth_date"]  # 日期部分匹配即可（忽略时区）


def test_increment_divination_count(memory_service: MemoryService, test_user: User) -> None:
    """测试增加占卜次数统计"""
    # 先创建画像
    memory_service.update_profile(user_id=test_user.id, gender="男")
    
    # 增加占卜次数
    memory_service.increment_divination_count(user_id=test_user.id)
    memory_service.increment_divination_count(user_id=test_user.id)
    
    profile = memory_service.get_user_profile(user_id=test_user.id)
    assert profile["total_divinations"] == 2


def test_increment_conversation_count(memory_service: MemoryService, test_user: User) -> None:
    """测试增加对话次数统计"""
    # 先创建画像
    memory_service.update_profile(user_id=test_user.id, gender="女")
    
    # 增加对话次数
    memory_service.increment_conversation_count(user_id=test_user.id)
    memory_service.increment_conversation_count(user_id=test_user.id)
    memory_service.increment_conversation_count(user_id=test_user.id)
    
    profile = memory_service.get_user_profile(user_id=test_user.id)
    assert profile["total_conversations"] == 3


def test_get_conversation_summary_not_exists(memory_service: MemoryService) -> None:
    """测试获取不存在的对话摘要"""
    summary = memory_service.get_conversation_summary(user_id=99999)
    assert summary is None


def test_create_conversation_summary(memory_service: MemoryService, test_user: User) -> None:
    """测试创建对话摘要"""
    summary = memory_service.update_summary(
        user_id=test_user.id,
        summary_text="用户问了关于事业发展的问题",
        keywords=["事业", "发展"],
        increment_messages=2,
        increment_divinations=1
    )
    
    assert summary is not None
    assert summary["user_id"] == test_user.id
    assert "事业发展" in summary["summary_text"]
    assert summary["keywords"] == ["事业", "发展"]
    assert summary["total_messages"] == 2
    assert summary["divination_count"] == 1


def test_append_to_conversation_summary(memory_service: MemoryService, test_user: User) -> None:
    """测试追加对话摘要"""
    # 先创建初始摘要
    memory_service.update_summary(
        user_id=test_user.id,
        summary_text="第一次对话：询问财运",
        keywords=["财运"],
        increment_messages=1,
        increment_divinations=1
    )
    
    # 追加新摘要
    updated_summary = memory_service.update_summary(
        user_id=test_user.id,
        summary_text="第二次对话：询问感情",
        keywords=["感情"],
        increment_messages=1,
        increment_divinations=1
    )
    
    assert "第一次对话：询问财运" in updated_summary["summary_text"]
    assert "第二次对话：询问感情" in updated_summary["summary_text"]
    assert updated_summary["total_messages"] == 2
    assert updated_summary["divination_count"] == 2


def test_conversation_summary_compression(memory_service: MemoryService, test_user: User) -> None:
    """测试对话摘要超过 1000 字符时的压缩"""
    # 创建初始摘要（接近 1000 字符）
    long_text = "用户询问事业发展问题。" * 50  # 约 600 字符
    memory_service.update_summary(
        user_id=test_user.id,
        summary_text=long_text,
        increment_messages=1
    )
    
    # 追加更多文本（触发压缩）
    more_text = "用户继续询问财运和感情问题。" * 40  # 约 640 字符
    compressed_summary = memory_service.update_summary(
        user_id=test_user.id,
        summary_text=more_text,
        increment_messages=1
    )
    
    # 验证摘要长度被控制
    assert len(compressed_summary["summary_text"]) <= 1020  # 允许少量超出
    assert "历史摘要已压缩" in compressed_summary["summary_text"]


def test_get_all_summaries(memory_service: MemoryService, test_user: User, db_session: Session) -> None:
    """测试获取所有对话摘要"""
    # 创建多个摘要（手动插入以模拟不同时间段）
    for i in range(3):
        summary = ConversationSummary(
            user_id=test_user.id,
            summary_text=f"对话摘要 {i+1}",
            keywords=[f"关键词{i+1}"],
            total_messages=i+1,
            divination_count=i,
            start_time=datetime(2024, 1, i+1),
            end_time=datetime(2024, 1, i+1, 23, 59)
        )
        db_session.add(summary)
    db_session.commit()
    
    # 查询所有摘要
    summaries = memory_service.get_all_summaries(user_id=test_user.id, limit=10)
    
    assert len(summaries) == 3
    # 验证按时间倒序（最新的在前）
    assert summaries[0]["summary_text"] == "对话摘要 3"
    assert summaries[1]["summary_text"] == "对话摘要 2"
    assert summaries[2]["summary_text"] == "对话摘要 1"


def test_get_all_summaries_with_limit(memory_service: MemoryService, test_user: User, db_session: Session) -> None:
    """测试限制返回数量的摘要查询"""
    # 创建 5 个摘要
    for i in range(5):
        summary = ConversationSummary(
            user_id=test_user.id,
            summary_text=f"对话摘要 {i+1}",
            total_messages=1,
            divination_count=0,
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 1)
        )
        db_session.add(summary)
    db_session.commit()
    
    # 限制返回 3 个
    summaries = memory_service.get_all_summaries(user_id=test_user.id, limit=3)
    
    assert len(summaries) == 3
