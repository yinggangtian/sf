"""集成测试：DivinationService 占卜服务层"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Generator, cast

import importlib

pytest = importlib.import_module("pytest")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.ai_agents.agents.registry import bootstrap_default_adapters, registry
from backend.ai_agents.services.divination_service import DivinationService
from backend.ai_agents.xlr.adapters.liuren_adapter import LiurenAdapter
from backend.ai_agents.xlr.liuren.utils import KnowledgeBase
from backend.shared.config.settings import get_settings
from backend.shared.db.models.divination import DivinationRecord
from backend.shared.db.models.knowledge import DiZhi, Gong, Qin, Shou, WuxingRelation
from backend.shared.db.models.user import User


@pytest.fixture(name="db_session")
def db_session_fixture() -> Generator[Session, None, None]:
    """创建测试数据库会话"""
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    
    # 确保测试前清空相关表
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(name="knowledge_base")
def knowledge_base_fixture(db_session: Session) -> KnowledgeBase:
    """从数据库加载知识库"""
    kb = KnowledgeBase()
    
    kb.load_gong_data(db_session.query(Gong).order_by(Gong.position).all())
    kb.load_shou_data(db_session.query(Shou).order_by(Shou.position).all())
    kb.load_qin_data(db_session.query(Qin).all())
    kb.load_dizhi_data(db_session.query(DiZhi).order_by(DiZhi.order).all())
    
    relations: Dict[str, Dict[str, str]] = {}
    for record in db_session.query(WuxingRelation).all():
        element1 = str(record.element1)
        element2 = str(record.element2)
        relation = str(record.relation)
        relations.setdefault(element1, {})[element2] = relation
    
    kb.load_wuxing_relations(relations)
    
    return kb


@pytest.fixture(name="test_user_id")
def test_user_id_fixture(db_session: Session) -> int:
    """创建或获取测试用户"""
    user = db_session.query(User).filter(User.username == "test_user").first()
    if not user:
        user = User(username="test_user", email="test@example.com", password_hash="dummy")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return cast(int, user.id)


@pytest.fixture(name="divination_service")
def divination_service_fixture(
    knowledge_base: KnowledgeBase,
    db_session: Session
) -> DivinationService:
    """创建占卜服务实例"""
    registry.clear()
    bootstrap_default_adapters(knowledge_base)
    adapter = registry.get("xlr-liuren")
    
    if adapter is None:
        raise RuntimeError("未能加载 xlr-liuren 适配器")
    
    if not isinstance(adapter, LiurenAdapter):
        raise RuntimeError("适配器类型不正确")
    
    return DivinationService(adapter, db_session)


@pytest.fixture(autouse=True)
def clear_test_records(db_session: Session, test_user_id: int) -> Generator[None, None, None]:
    """测试前后清理测试数据"""
    yield
    # 测试后清理
    db_session.query(DivinationRecord).filter(
        DivinationRecord.user_id == test_user_id
    ).delete()
    db_session.commit()


def test_perform_divination_complete_flow(
    divination_service: DivinationService,
    test_user_id: int,
    db_session: Session
) -> None:
    """测试完整占卜流程（槽位验证 → 起卦 → 解卦 → 保存 → 返回）"""
    result = divination_service.perform_divination(
        user_id=test_user_id,
        num1=3,
        num2=5,
        gender="男",
        ask_time=datetime(2024, 5, 10, 10, 0, 0),
        question_type="事业"
    )
    
    # 验证返回格式
    assert "result" in result
    assert "interpretation" in result
    assert "meta" in result
    
    # 验证 result 字段
    assert "paipan_result" in result["result"]
    assert "interpretation_result" in result["result"]
    assert "record_id" in result["result"]
    
    # 验证 meta 字段
    assert result["meta"]["algorithm"] == "xlr-liuren"
    assert result["meta"]["user_id"] == test_user_id
    assert result["meta"]["question_type"] == "事业"
    assert result["meta"]["gender"] == "男"
    
    # 验证数据库记录已保存
    record = db_session.query(DivinationRecord).filter(
        DivinationRecord.id == result["result"]["record_id"]
    ).first()
    
    assert record is not None
    assert cast(int, record.user_id) == test_user_id
    assert cast(str, record.question_type) == "事业"
    assert cast(str, record.gender) == "男"
    assert record.qigua_data is not None
    assert record.paipan_data is not None
    assert record.interpretation_data is not None


def test_perform_divination_slot_validation_num1_out_of_range(
    divination_service: DivinationService,
    test_user_id: int
) -> None:
    """测试槽位验证：num1 超出范围"""
    with pytest.raises(ValueError, match="第一个报数必须在 1-6 之间"):
        divination_service.perform_divination(
            user_id=test_user_id,
            num1=9,
            num2=5,
            gender="男",
            ask_time=datetime(2024, 5, 10, 10, 0, 0),
            question_type="事业"
        )


def test_perform_divination_slot_validation_num2_out_of_range(
    divination_service: DivinationService,
    test_user_id: int
) -> None:
    """测试槽位验证：num2 超出范围"""
    with pytest.raises(ValueError, match="第二个报数必须在 1-6 之间"):
        divination_service.perform_divination(
            user_id=test_user_id,
            num1=3,
            num2=0,
            gender="男",
            ask_time=datetime(2024, 5, 10, 10, 0, 0),
            question_type="事业"
        )


def test_perform_divination_slot_validation_invalid_gender(
    divination_service: DivinationService,
    test_user_id: int
) -> None:
    """测试槽位验证：性别无效"""
    with pytest.raises(ValueError, match="性别必须是 '男' 或 '女'"):
        divination_service.perform_divination(
            user_id=test_user_id,
            num1=3,
            num2=5,
            gender="未知",
            ask_time=datetime(2024, 5, 10, 10, 0, 0),
            question_type="事业"
        )


def test_perform_divination_slot_validation_future_time(
    divination_service: DivinationService,
    test_user_id: int
) -> None:
    """测试槽位验证：未来时间"""
    future_time = datetime(2099, 12, 31, 23, 59, 59)
    with pytest.raises(ValueError, match="起卦时间不能是未来时间"):
        divination_service.perform_divination(
            user_id=test_user_id,
            num1=3,
            num2=5,
            gender="男",
            ask_time=future_time,
            question_type="事业"
        )


def test_perform_divination_slot_validation_empty_question_type(
    divination_service: DivinationService,
    test_user_id: int
) -> None:
    """测试槽位验证：问题类型为空"""
    with pytest.raises(ValueError, match="问题类型不能为空"):
        divination_service.perform_divination(
            user_id=test_user_id,
            num1=3,
            num2=5,
            gender="男",
            ask_time=datetime(2024, 5, 10, 10, 0, 0),
            question_type=""
        )


def test_get_history_returns_paginated_records(
    divination_service: DivinationService,
    test_user_id: int
) -> None:
    """测试历史记录查询：返回分页记录"""
    # 先创建几条记录
    for i in range(5):
        divination_service.perform_divination(
            user_id=test_user_id,
            num1=3,
            num2=5,
            gender="男",
            ask_time=datetime(2024, 5, 10 + i, 10, 0, 0),
            question_type=f"问题{i + 1}"
        )
    
    # 查询第一页（每页3条）
    result = divination_service.get_history(
        user_id=test_user_id,
        page=1,
        page_size=3
    )
    
    assert "items" in result
    assert "total" in result
    assert "page" in result
    assert "page_size" in result
    assert "has_more" in result
    
    assert len(result["items"]) == 3
    assert result["total"] == 5
    assert result["page"] == 1
    assert result["page_size"] == 3
    assert result["has_more"] is True
    
    # 查询第二页
    result_page2 = divination_service.get_history(
        user_id=test_user_id,
        page=2,
        page_size=3
    )
    
    assert len(result_page2["items"]) == 2
    assert result_page2["has_more"] is False


def test_get_history_filters_by_question_type(
    divination_service: DivinationService,
    test_user_id: int
) -> None:
    """测试历史记录查询：按问题类型筛选"""
    # 创建不同类型的记录
    divination_service.perform_divination(
        user_id=test_user_id,
        num1=3,
        num2=5,
        gender="男",
        ask_time=datetime(2024, 5, 10, 10, 0, 0),
        question_type="事业"
    )
    divination_service.perform_divination(
        user_id=test_user_id,
        num1=2,
        num2=4,
        gender="女",
        ask_time=datetime(2024, 5, 11, 10, 0, 0),
        question_type="感情"
    )
    divination_service.perform_divination(
        user_id=test_user_id,
        num1=1,
        num2=6,
        gender="男",
        ask_time=datetime(2024, 5, 12, 10, 0, 0),
        question_type="事业"
    )
    
    # 筛选"事业"类型
    result = divination_service.get_history(
        user_id=test_user_id,
        question_type="事业"
    )
    
    assert result["total"] == 2
    assert all(item["question_type"] == "事业" for item in result["items"])


def test_get_statistics_aggregates_correctly(
    divination_service: DivinationService,
    test_user_id: int
) -> None:
    """测试统计功能：正确聚合占卜次数和问题类型"""
    # 创建多条记录
    divination_service.perform_divination(
        user_id=test_user_id,
        num1=3,
        num2=5,
        gender="男",
        ask_time=datetime(2024, 5, 10, 10, 0, 0),
        question_type="事业"
    )
    divination_service.perform_divination(
        user_id=test_user_id,
        num1=2,
        num2=4,
        gender="女",
        ask_time=datetime(2024, 5, 11, 10, 0, 0),
        question_type="感情"
    )
    divination_service.perform_divination(
        user_id=test_user_id,
        num1=1,
        num2=6,
        gender="男",
        ask_time=datetime(2024, 6, 12, 10, 0, 0),
        question_type="事业"
    )
    
    stats = divination_service.get_statistics(test_user_id)
    
    assert stats["total_count"] == 3
    assert stats["question_type_distribution"]["事业"] == 2
    assert stats["question_type_distribution"]["感情"] == 1
    assert stats["most_common_type"] == "事业"
    assert stats["first_divination"] is not None
    assert stats["last_divination"] is not None
    # Monthly distribution uses actual DB created_at timestamp (server time)
    assert len(stats["monthly_distribution"]) > 0


def test_get_statistics_empty_history(
    divination_service: DivinationService,
    db_session: Session
) -> None:
    """测试统计功能：无历史记录时返回空统计"""
    # 创建一个新用户（无历史记录）- 使用时间戳确保唯一性
    from time import time
    unique_suffix = str(int(time() * 1000))
    new_user = User(
        username=f"empty_user_{unique_suffix}",
        email=f"empty_{unique_suffix}@example.com",
        password_hash="dummy"
    )
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)
    
    try:
        stats = divination_service.get_statistics(cast(int, new_user.id))
        
        assert stats["total_count"] == 0
        assert stats["question_type_distribution"] == {}
        assert stats["most_common_type"] is None
        assert stats["first_divination"] is None
        assert stats["last_divination"] is None
        assert stats["monthly_distribution"] == {}
    finally:
        # 清理
        db_session.delete(new_user)
        db_session.commit()
