"""数据库初始化脚本

该脚本用于创建数据库表并加载基础数据，支持幂等执行。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple, Type

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

# 先将项目根目录加入模块搜索路径
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.shared.config.settings import get_settings  # noqa: E402
from backend.shared.db import models as db_models  # noqa: E402,F401
from backend.shared.db.base import Base  # noqa: E402
from backend.shared.db.models import knowledge as knowledge_models  # noqa: E402
from backend.shared.db.models.user import User  # noqa: E402

LOGGER = logging.getLogger("init_database")


# ==================== 静态数据定义 ====================

GONG_DATA: List[Dict[str, Any]] = [
    {
        "name": "大安",
        "position": 1,
        "wuxing": "木",
        "meaning": "主安定吉祥，宜静待时机，凡事以稳为先。",
        "attributes": {"direction": "东北", "keyword": "稳定"},
    },
    {
        "name": "留连",
        "position": 2,
        "wuxing": "水",
        "meaning": "主反复迟缓，进展受阻，多留意纠缠之事。",
        "attributes": {"direction": "北方", "keyword": "拖延"},
    },
    {
        "name": "速喜",
        "position": 3,
        "wuxing": "金",
        "meaning": "主事情顺遂，利于快速推进，宜把握机会。",
        "attributes": {"direction": "西方", "keyword": "捷报"},
    },
    {
        "name": "赤口",
        "position": 4,
        "wuxing": "火",
        "meaning": "主口舌是非，宜避免争执冲突，谨言慎行。",
        "attributes": {"direction": "南方", "keyword": "口舌"},
    },
    {
        "name": "小吉",
        "position": 5,
        "wuxing": "木",
        "meaning": "主小有收获，宜循序渐进，积小成多。",
        "attributes": {"direction": "东南", "keyword": "稳进"},
    },
    {
        "name": "空亡",
        "position": 6,
        "wuxing": "土",
        "meaning": "主虚耗延迟，宜审慎评估，避免盲目投入。",
        "attributes": {"direction": "中宫", "keyword": "停滞"},
    },
]

SHOU_DATA: List[Dict[str, Any]] = [
    {
        "name": "青龙",
        "position": 1,
        "wuxing": "木",
        "characteristics": "象征吉庆与贵人，善于开创与协调。",
        "meaning": "遇事多得助力，宜主动争取资源。",
        "attributes": {"nature": "阳", "talent": "创造"},
    },
    {
        "name": "朱雀",
        "position": 2,
        "wuxing": "火",
        "characteristics": "象征表达与声望，擅长沟通传播。",
        "meaning": "利于陈述表达，谨防口舌纷争。",
        "attributes": {"nature": "阳", "talent": "表达"},
    },
    {
        "name": "勾陈",
        "position": 3,
        "wuxing": "土",
        "characteristics": "象征稳重与守成，擅长落地执行。",
        "meaning": "宜稳扎稳打，留意守成与维护。",
        "attributes": {"nature": "阴", "talent": "执行"},
    },
    {
        "name": "腾蛇",
        "position": 4,
        "wuxing": "火",
        "characteristics": "象征灵动与变化，善于应变与想象。",
        "meaning": "适合脑力创意，需防虚幻不实。",
        "attributes": {"nature": "阴", "talent": "创意"},
    },
    {
        "name": "白虎",
        "position": 5,
        "wuxing": "金",
        "characteristics": "象征果断与力量，行动迅捷果敢。",
        "meaning": "利于果断出击，注意安全与风险。",
        "attributes": {"nature": "阳", "talent": "决断"},
    },
    {
        "name": "玄武",
        "position": 6,
        "wuxing": "水",
        "characteristics": "象征智慧与潜藏，善于谋略谨慎。",
        "meaning": "宜深度思考，注意保守机密。",
        "attributes": {"nature": "阴", "talent": "谋略"},
    },
]

QIN_DATA: List[Dict[str, Any]] = [
    {
        "name": "父母",
        "relationship": "长辈权威",
        "meaning": "象征长辈、文书、房屋，强调支持与庇护。",
        "usage_context": "求学、合同、长辈相关事项。",
        "attributes": {"element": "木"},
    },
    {
        "name": "兄弟",
        "relationship": "同辈伙伴",
        "meaning": "象征同辈与协作，也提示竞争与分担。",
        "usage_context": "合作、团队、人际协调。",
        "attributes": {"element": "金"},
    },
    {
        "name": "官鬼",
        "relationship": "职责压力",
        "meaning": "象征权力、工作压力、病灾等制约力量。",
        "usage_context": "事业、官司、健康预警。",
        "attributes": {"element": "土"},
    },
    {
        "name": "妻财",
        "relationship": "财富伴侣",
        "meaning": "象征财务资源与伴侣关系，强调收益与占有。",
        "usage_context": "财运、感情、投资决策。",
        "attributes": {"element": "水"},
    },
    {
        "name": "子孙",
        "relationship": "成果晚辈",
        "meaning": "象征子女、创造力与成果结实。",
        "usage_context": "育儿、创作、项目收尾。",
        "attributes": {"element": "火"},
    },
    {
        "name": "贵人",
        "relationship": "助力支援",
        "meaning": "象征外部支援与机会把握。",
        "usage_context": "寻求资源、拓展人脉、关键节点。",
        "attributes": {"element": "土"},
    },
]

DIZHI_DATA: List[Dict[str, Any]] = [
    {"name": "子", "order": 1, "wuxing": "水", "shichen": "子时(23:00-01:00)", "meaning": "动中有静，蕴育萌芽之象。"},
    {"name": "丑", "order": 2, "wuxing": "土", "shichen": "丑时(01:00-03:00)", "meaning": "稳重守成，利于积蓄力量。"},
    {"name": "寅", "order": 3, "wuxing": "木", "shichen": "寅时(03:00-05:00)", "meaning": "万物萌动，适合计划启动。"},
    {"name": "卯", "order": 4, "wuxing": "木", "shichen": "卯时(05:00-07:00)", "meaning": "日出东方，宜主动争先。"},
    {"name": "辰", "order": 5, "wuxing": "土", "shichen": "辰时(07:00-09:00)", "meaning": "龙腾云起，适合整合资源。"},
    {"name": "巳", "order": 6, "wuxing": "火", "shichen": "巳时(09:00-11:00)", "meaning": "阳气隆盛，利于对外拓展。"},
    {"name": "午", "order": 7, "wuxing": "火", "shichen": "午时(11:00-13:00)", "meaning": "盛极而炽，注意张弛有度。"},
    {"name": "未", "order": 8, "wuxing": "土", "shichen": "未时(13:00-15:00)", "meaning": "缓中带稳，宜调整节奏。"},
    {"name": "申", "order": 9, "wuxing": "金", "shichen": "申时(15:00-17:00)", "meaning": "收敛内化，利于整理总结。"},
    {"name": "酉", "order": 10, "wuxing": "金", "shichen": "酉时(17:00-19:00)", "meaning": "夕阳西下，宜沉淀思考。"},
    {"name": "戌", "order": 11, "wuxing": "土", "shichen": "戌时(19:00-21:00)", "meaning": "守成整理，适合内务处理。"},
    {"name": "亥", "order": 12, "wuxing": "水", "shichen": "亥时(21:00-23:00)", "meaning": "万物潜藏，宜修养身心。"},
]

TIANGAN_DATA: List[Dict[str, Any]] = [
    {"name": "甲", "order": 1, "wuxing": "木", "yin_yang": "阳", "meaning": "阳木之始，象征破土萌芽。", "attributes": {"direction": "东方"}},
    {"name": "乙", "order": 2, "wuxing": "木", "yin_yang": "阴", "meaning": "阴木柔顺，象征滋养生机。", "attributes": {"direction": "东方"}},
    {"name": "丙", "order": 3, "wuxing": "火", "yin_yang": "阳", "meaning": "阳火炽盛，象征光明外放。", "attributes": {"direction": "南方"}},
    {"name": "丁", "order": 4, "wuxing": "火", "yin_yang": "阴", "meaning": "阴火温润，象征照拂关怀。", "attributes": {"direction": "南方"}},
    {"name": "戊", "order": 5, "wuxing": "土", "yin_yang": "阳", "meaning": "阳土厚重，象征承载稳定。", "attributes": {"direction": "中央"}},
    {"name": "己", "order": 6, "wuxing": "土", "yin_yang": "阴", "meaning": "阴土细腻，象征培育孕育。", "attributes": {"direction": "中央"}},
    {"name": "庚", "order": 7, "wuxing": "金", "yin_yang": "阳", "meaning": "阳金刚健，象征果断肃杀。", "attributes": {"direction": "西方"}},
    {"name": "辛", "order": 8, "wuxing": "金", "yin_yang": "阴", "meaning": "阴金清丽，象征精炼修整。", "attributes": {"direction": "西方"}},
    {"name": "壬", "order": 9, "wuxing": "水", "yin_yang": "阳", "meaning": "阳水豪迈，象征流动包容。", "attributes": {"direction": "北方"}},
    {"name": "癸", "order": 10, "wuxing": "水", "yin_yang": "阴", "meaning": "阴水静谧，象征滋润蓄藏。", "attributes": {"direction": "北方"}},
]

WUXING_RELATIONS: List[Dict[str, Any]] = [
    {"element1": "金", "element2": "木", "relation": "克", "description": "金伐木，利断舍离。"},
    {"element1": "金", "element2": "水", "relation": "生", "description": "金生水，推陈出新。"},
    {"element1": "金", "element2": "火", "relation": "克我", "description": "火克金，需防冲击。"},
    {"element1": "金", "element2": "土", "relation": "生我", "description": "土生金，稳步积累。"},
    {"element1": "金", "element2": "金", "relation": "同", "description": "同类相助。"},
    {"element1": "木", "element2": "火", "relation": "生", "description": "木生火，蓬勃向上。"},
    {"element1": "木", "element2": "土", "relation": "克", "description": "木克土，打破僵局。"},
    {"element1": "木", "element2": "金", "relation": "克我", "description": "金克木，警惕阻力。"},
    {"element1": "木", "element2": "水", "relation": "生我", "description": "水生木，充足养分。"},
    {"element1": "木", "element2": "木", "relation": "同", "description": "同气连枝。"},
    {"element1": "水", "element2": "木", "relation": "生", "description": "水生木，助力成长。"},
    {"element1": "水", "element2": "火", "relation": "克", "description": "水克火，降温灭燥。"},
    {"element1": "水", "element2": "土", "relation": "克我", "description": "土克水，谨防束缚。"},
    {"element1": "水", "element2": "金", "relation": "生我", "description": "金生水，资源输入。"},
    {"element1": "水", "element2": "水", "relation": "同", "description": "同源共流。"},
    {"element1": "火", "element2": "土", "relation": "生", "description": "火生土，催化成果。"},
    {"element1": "火", "element2": "金", "relation": "克", "description": "火克金，需防过激。"},
    {"element1": "火", "element2": "水", "relation": "克我", "description": "水克火，注意调和。"},
    {"element1": "火", "element2": "木", "relation": "生我", "description": "木生火，积蓄势能。"},
    {"element1": "火", "element2": "火", "relation": "同", "description": "同类共鸣。"},
    {"element1": "土", "element2": "金", "relation": "生", "description": "土生金，凝聚成果。"},
    {"element1": "土", "element2": "水", "relation": "克", "description": "土克水，防止流失。"},
    {"element1": "土", "element2": "木", "relation": "克我", "description": "木克土，需固本。"},
    {"element1": "土", "element2": "火", "relation": "生我", "description": "火生土，成果沉淀。"},
    {"element1": "土", "element2": "土", "relation": "同", "description": "同根互助。"},
]

TEST_USER_DATA: Dict[str, Any] = {
    "id": 1,
    "username": "test_user",
    "email": "test_user@example.com",
    "password_hash": "$2b$12$5KEBz1qv0pO2XHl2i3aMHOJ0bbKt01sYzj9GZA0PWT8kAAZpE7aV2",
    "is_active": True,
    "is_verified": False,
}


# ==================== 数据写入逻辑 ====================

def seed_records(
    session: Session,
    model: Type[Any],
    data: Sequence[Dict[str, Any]],
    unique_fields: Iterable[str],
) -> Tuple[int, int]:
    """根据唯一字段插入或更新记录，返回(新增数, 更新数)。"""
    inserted = 0
    updated = 0

    for payload in data:
        filters = {field: payload[field] for field in unique_fields}
        instance = session.query(model).filter_by(**filters).one_or_none()

        if instance is None:
            session.add(model(**payload))
            inserted += 1
        else:
            dirty = False
            for key, value in payload.items():
                if getattr(instance, key) != value:
                    setattr(instance, key, value)
                    dirty = True
            if dirty:
                updated += 1

    return inserted, updated


def seed_knowledge(session: Session) -> None:
    """写入基础知识库数据。"""
    stats = {}
    stats["liu_gong"] = seed_records(session, knowledge_models.Gong, GONG_DATA, ("name",))
    stats["liu_shou"] = seed_records(session, knowledge_models.Shou, SHOU_DATA, ("name",))
    stats["liu_qin"] = seed_records(session, knowledge_models.Qin, QIN_DATA, ("name",))
    stats["di_zhi"] = seed_records(session, knowledge_models.DiZhi, DIZHI_DATA, ("name",))
    stats["tian_gan"] = seed_records(session, knowledge_models.TianGan, TIANGAN_DATA, ("name",))
    stats["wuxing_relations"] = seed_records(session, knowledge_models.WuxingRelation, WUXING_RELATIONS, ("element1", "element2"))

    for table, (inserted, updated) in stats.items():
        LOGGER.info("%s: inserted=%d, updated=%d", table, inserted, updated)


def seed_test_user(session: Session) -> None:
    """创建或更新测试用户。"""
    existing = session.query(User).filter(User.id == TEST_USER_DATA["id"]).one_or_none()

    if existing is None:
        session.add(User(**TEST_USER_DATA))
        LOGGER.info("Created test user with id=%s", TEST_USER_DATA["id"])
    else:
        dirty = False
        for field, value in TEST_USER_DATA.items():
            if getattr(existing, field) != value:
                setattr(existing, field, value)
                dirty = True
        if dirty:
            LOGGER.info("Updated test user with id=%s", TEST_USER_DATA["id"])
        else:
            LOGGER.info("Test user id=%s already up-to-date", TEST_USER_DATA["id"])


def validate_data_integrity(session: Session) -> None:
    """验证知识库关键数据量是否达标。"""
    session.flush()

    gong_count = session.query(knowledge_models.Gong).count()
    shou_count = session.query(knowledge_models.Shou).count()

    LOGGER.info("Integrity check: liu_gong=%d, liu_shou=%d", gong_count, shou_count)

    if gong_count != 6:
        raise RuntimeError(f"预期 6 条六宫数据，实际 {gong_count}")
    if shou_count != 6:
        raise RuntimeError(f"预期 6 条六兽数据，实际 {shou_count}")


def create_session() -> sessionmaker:
    """创建数据库会话工厂。"""
    settings = get_settings()
    LOGGER.info("Connecting to database: %s", settings.database_url)

    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        future=True,
    )

    LOGGER.info("Ensuring tables exist: %s", ", ".join(sorted(Base.metadata.tables.keys())))
    Base.metadata.create_all(bind=engine)

    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def init_database() -> None:
    """执行数据库初始化流程。"""
    SessionLocal = create_session()

    with SessionLocal() as session:
        try:
            with session.begin():
                seed_knowledge(session)
                seed_test_user(session)
                validate_data_integrity(session)
        except Exception:
            LOGGER.exception("数据库初始化失败，事务已回滚")
            raise

    LOGGER.info("数据库初始化完成")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def main() -> None:
    configure_logging()

    try:
        init_database()
    except SQLAlchemyError as exc:
        LOGGER.error("SQLAlchemy 错误: %s", exc)
        raise SystemExit(1) from exc
    except Exception as exc:
        LOGGER.error("初始化过程中出现异常: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
