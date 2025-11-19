"""算法适配器注册与路由的集成测试。"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, cast

import importlib

pytest = importlib.import_module("pytest")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai_agents.agents.registry import bootstrap_default_adapters, registry
from backend.ai_agents.xlr.adapters.liuren_adapter import LiurenAdapter
from backend.ai_agents.xlr.liuren.utils import KnowledgeBase
from backend.shared.config.settings import get_settings
from backend.shared.db.models.knowledge import DiZhi, Gong, Qin, Shou, WuxingRelation


@pytest.fixture(name="knowledge_base")
def knowledge_base_fixture() -> KnowledgeBase:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    kb = KnowledgeBase()

    with SessionLocal() as session:
        kb.load_gong_data(session.query(Gong).order_by(Gong.position).all())
        kb.load_shou_data(session.query(Shou).order_by(Shou.position).all())
        kb.load_qin_data(session.query(Qin).all())
        kb.load_dizhi_data(session.query(DiZhi).order_by(DiZhi.order).all())

        relations: Dict[str, Dict[str, str]] = {}
        for record in session.query(WuxingRelation).all():
            element1 = cast(str, record.element1)
            element2 = cast(str, record.element2)
            relation = cast(str, record.relation)
            relations.setdefault(element1, {})[element2] = relation

        kb.load_wuxing_relations(relations)

    return kb


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    registry.clear()


def test_register_and_retrieve_liuren_adapter(knowledge_base: KnowledgeBase) -> None:
    adapter = LiurenAdapter(knowledge_base)
    registry.register(adapter)

    retrieved = registry.get("xlr-liuren")
    assert retrieved is adapter


def test_route_with_hint_returns_correct_adapter(knowledge_base: KnowledgeBase) -> None:
    adapter = LiurenAdapter(knowledge_base)
    registry.register(adapter)

    routed = registry.route("xlr-liuren")
    assert routed is adapter


def test_route_without_hint_returns_none(knowledge_base: KnowledgeBase) -> None:
    adapter = LiurenAdapter(knowledge_base)
    registry.register(adapter)

    assert registry.route(None) is None


def test_bootstrap_registers_default_adapter(knowledge_base: KnowledgeBase) -> None:
    bootstrap_default_adapters(knowledge_base)
    assert registry.get("xlr-liuren") is not None


def test_standardized_output_schema(knowledge_base: KnowledgeBase) -> None:
    adapter = LiurenAdapter(knowledge_base)
    registry.register(adapter)

    schema = adapter.get_output_schema()
    assert set(schema.keys()) == {"qigua", "jiegua", "find_object"}
    assert schema["qigua"]["paipan_result"] == "PaipanResult object"


def test_validate_input_enforces_ranges(knowledge_base: KnowledgeBase) -> None:
    adapter = LiurenAdapter(knowledge_base)
    registry.register(adapter)

    with pytest.raises(ValueError):
        adapter.validate_input({"operation": "qigua", "number1": 9, "number2": 1})

    assert adapter.validate_input({"operation": "qigua", "number1": 3, "number2": 5})


def test_adapter_run_outputs_uniform_structure(knowledge_base: KnowledgeBase) -> None:
    adapter = LiurenAdapter(knowledge_base)
    registry.register(adapter)

    qigua_result = adapter.run(
        {
            "operation": "qigua",
            "number1": 3,
            "number2": 5,
            "qigua_time": datetime(2024, 5, 10, 10, 0, 0),
        }
    )

    assert qigua_result["operation"] == "qigua"
    assert "paipan_result" in qigua_result

    jiegua_result = adapter.run(
        {
            "operation": "jiegua",
            "paipan_result": qigua_result["paipan_result"],
            "question_type": "事业",
            "gender": "男",
        }
    )

    assert jiegua_result["operation"] == "jiegua"
    assert "interpretation_result" in jiegua_result