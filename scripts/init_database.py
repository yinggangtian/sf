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
        "attributes": {
            "direction": "东方",
            "keyword": "稳定",
            "symbol": "安稳平静",
            "nature": "上吉",
            "color": "青绿色",
            "number": "1、8",
            "body_part": "肝胆",
            "emotion": "喜悦、平和",
            "advice": "万事大吉，可放心进行，稳定发展"
        },
    },
    {
        "name": "留连",
        "position": 2,
        "wuxing": "火",
        "meaning": "主反复迟缓，进展受阻，多留意纠缠之事。",
        "attributes": {
            "direction": "南方",
            "keyword": "拖延",
            "symbol": "延迟变动",
            "nature": "凶中带吉",
            "color": "红色",
            "number": "2、9",
            "body_part": "心小肠",
            "emotion": "焦虑、期待",
            "advice": "需耐心等待，不宜急躁，曲折中有希望"
        },
    },
    {
        "name": "速喜",
        "position": 3,
        "wuxing": "火",
        "meaning": "主事情顺遂，利于快速推进，宜把握机会。",
        "attributes": {
            "direction": "南方",
            "keyword": "捷报",
            "symbol": "快速喜庆",
            "nature": "上吉",
            "color": "明亮红色",
            "number": "3、7",
            "body_part": "心脏",
            "emotion": "欢喜、热情",
            "advice": "好消息即将到来，顺利成功，喜事临门"
        },
    },
    {
        "name": "赤口",
        "position": 4,
        "wuxing": "金",
        "meaning": "主口舌是非，宜避免争执冲突，谨言慎行。",
        "attributes": {
            "direction": "西方",
            "keyword": "口舌",
            "symbol": "争端口舌",
            "nature": "大凶",
            "color": "白色",
            "number": "4、9",
            "body_part": "肺大肠",
            "emotion": "愤怒、激动",
            "advice": "慎言慎行，避免冲突，防止口舌之争"
        },
    },
    {
        "name": "小吉",
        "position": 5,
        "wuxing": "水",
        "meaning": "主小有收获，宜循序渐进，积小成多。",
        "attributes": {
            "direction": "北方",
            "keyword": "稳进",
            "symbol": "小有所成",
            "nature": "吉中带凶",
            "color": "黑色",
            "number": "5、10",
            "body_part": "肾膀胱",
            "emotion": "谨慎、冷静",
            "advice": "小有所成，不可贪大求全，稳中求进"
        },
    },
    {
        "name": "空亡",
        "position": 6,
        "wuxing": "土",
        "meaning": "主虚耗延迟，宜审慎评估，避免盲目投入。",
        "attributes": {
            "direction": "中央",
            "keyword": "停滞",
            "symbol": "虚无空缺",
            "nature": "大凶",
            "color": "黄色",
            "number": "6、0",
            "body_part": "脾胃",
            "emotion": "忧郁、失落",
            "advice": "难有结果，虚耗精力，应及时调整或放弃"
        },
    },
]

SHOU_DATA: List[Dict[str, Any]] = [
    {
        "name": "青龙",
        "position": 1,
        "wuxing": "木",
        "characteristics": "高雅、威严、正直、主动",
        "meaning": "象征高贵、权威、贵人相助、文书喜讯",
        "attributes": {
            "nature": "阳",
            "talent": "创造",
            "symbol": "贵人、文书、喜讯",
            "color": "青绿色",
            "direction": "东方",
            "season": "春季",
            "best_time": "寅时(3-5点)",
            "advice": "不需化解，应把握机会，主动争取"
        },
    },
    {
        "name": "朱雀",
        "position": 2,
        "wuxing": "火",
        "characteristics": "活跃、多言、敏感、聪明",
        "meaning": "象征言语、文字、交流、灵活多变",
        "attributes": {
            "nature": "阳",
            "talent": "表达",
            "symbol": "口舌、是非、交通",
            "color": "红色",
            "direction": "南方",
            "season": "夏季",
            "best_time": "午时(11-13点)",
            "advice": "慎言慎行，避免争论，多做善事"
        },
    },
    {
        "name": "勾陈",
        "position": 3,
        "wuxing": "土",
        "characteristics": "稳重、忧郁、保守、压抑",
        "meaning": "象征阻滞、疾病、忧愁、压力",
        "attributes": {
            "nature": "阴",
            "talent": "执行",
            "symbol": "忧虑、疾病、阻碍",
            "color": "黄色",
            "direction": "中央",
            "season": "季末交接期",
            "best_time": "辰戌丑未时",
            "advice": "保持乐观，注意健康，不要强求"
        },
    },
    {
        "name": "腾蛇",
        "position": 4,
        "wuxing": "火",
        "characteristics": "多变、敏感、灵活、阴险",
        "meaning": "象征变化、惊吓、不安、转折",
        "attributes": {
            "nature": "阴",
            "talent": "创意",
            "symbol": "变动、惊恐、暗算",
            "color": "紫红色",
            "direction": "东南",
            "season": "夏季",
            "best_time": "巳时(9-11点)",
            "advice": "保持冷静，避免轻信，稳固为主"
        },
    },
    {
        "name": "白虎",
        "position": 5,
        "wuxing": "金",
        "characteristics": "刚猛、直接、凶狠、冲动",
        "meaning": "象征威猛、凶险、伤害、突发状况",
        "attributes": {
            "nature": "阳",
            "talent": "决断",
            "symbol": "凶险、伤害、官非",
            "color": "白色",
            "direction": "西方",
            "season": "秋季",
            "best_time": "申时(15-17点)",
            "advice": "谨慎行事，避免冲突，可佩戴吉祥物化解"
        },
    },
    {
        "name": "玄武",
        "position": 6,
        "wuxing": "水",
        "characteristics": "隐忍、谨慎、机智、自保",
        "meaning": "象征隐秘、盗窃、背叛、潜伏",
        "attributes": {
            "nature": "阴",
            "talent": "谋略",
            "symbol": "盗贼、暗昧、阴谋",
            "color": "黑色",
            "direction": "北方",
            "season": "冬季",
            "best_time": "子时(23-1点)",
            "advice": "提高警惕，检查安全，避免夜间活动"
        },
    },
]

QIN_DATA: List[Dict[str, Any]] = [
    {
        "name": "父母",
        "relationship": "长辈权威",
        "meaning": "代表长辈、保护、房产、学问",
        "usage_context": "家庭、学校、教育机构、房地产",
        "attributes": {
            "symbol": "保护、教导、照顾、居所、学问",
            "color": "棕色、土黄色",
            "direction": "东北方",
            "body_part": "脾胃、皮肤、肌肉",
            "emotion": "安心、依赖、尊敬、稳定"
        },
    },
    {
        "name": "兄弟",
        "relationship": "同辈伙伴",
        "meaning": "代表竞争、同辈、朋友、合作伙伴",
        "usage_context": "社交圈、团队项目、合作企业",
        "attributes": {
            "symbol": "平等、竞争、协作、交流、同辈",
            "color": "青绿色",
            "direction": "东方",
            "body_part": "肝胆、眼睛、肌腱",
            "emotion": "亲近、竞争、合作、信任"
        },
    },
    {
        "name": "官鬼",
        "relationship": "职责压力",
        "meaning": "代表外部权威、管理者、事业、压力",
        "usage_context": "工作、事业、官场、法律、管理层",
        "attributes": {
            "symbol": "权力、工作、压力、管理、限制",
            "color": "黑色、深蓝色",
            "direction": "正北方",
            "body_part": "骨骼、肾脏、耳朵",
            "emotion": "压力、紧张、严肃、敬畏"
        },
    },
    {
        "name": "妻财",
        "relationship": "财富伴侣",
        "meaning": "代表财运、钱财、情感",
        "usage_context": "财务、投资、银行、婚恋、商业",
        "attributes": {
            "symbol": "财富、收入、爱情、情感、资源",
            "color": "白色、金色",
            "direction": "西方",
            "body_part": "肺、大肠、皮肤",
            "emotion": "满足、喜爱、珍视、安心"
        },
    },
    {
        "name": "子孙",
        "relationship": "成果晚辈",
        "meaning": "代表喜庆、子女、学业、休闲",
        "usage_context": "家庭教育、文娱活动、节日庆典",
        "attributes": {
            "symbol": "收获、喜庆、后代、成就、放松",
            "color": "红色、粉色",
            "direction": "南方",
            "body_part": "心脏、小肠、面部",
            "emotion": "喜悦、放松、满足、成就感"
        },
    },
]

DIZHI_DATA: List[Dict[str, Any]] = [
    {"name": "子", "order": 1, "wuxing": "水", "shichen": "子时(23:00-01:00)", "meaning": "代表机密、聪明、流动性强，亦主狡猾、感情泛滥。"},
    {"name": "丑", "order": 2, "wuxing": "土", "shichen": "丑时(01:00-03:00)", "meaning": "代表金融、务实，亦主倔强、抱怨。"},
    {"name": "寅", "order": 3, "wuxing": "木", "shichen": "寅时(03:00-05:00)", "meaning": "代表官贵、清高、文化、智慧。"},
    {"name": "卯", "order": 4, "wuxing": "木", "shichen": "卯时(05:00-07:00)", "meaning": "代表交通、买卖、信息，主忠诚与灵活。"},
    {"name": "辰", "order": 5, "wuxing": "土", "shichen": "辰时(07:00-09:00)", "meaning": "代表医巫卜相、倔强、宗教人士。"},
    {"name": "巳", "order": 6, "wuxing": "火", "shichen": "巳时(09:00-11:00)", "meaning": "代表文书、消息、精明、多疑。"},
    {"name": "午", "order": 7, "wuxing": "火", "shichen": "午时(11:00-13:00)", "meaning": "代表荣誉、文艺、敏捷、冲动。"},
    {"name": "未", "order": 8, "wuxing": "土", "shichen": "未时(13:00-15:00)", "meaning": "代表皮肤、口食、辩论能力。"},
    {"name": "申", "order": 9, "wuxing": "金", "shichen": "申时(15:00-17:00)", "meaning": "代表武术、军人、执法。"},
    {"name": "酉", "order": 10, "wuxing": "金", "shichen": "酉时(17:00-19:00)", "meaning": "代表化妆品、美容、首饰。"},
    {"name": "戌", "order": 11, "wuxing": "土", "shichen": "戌时(19:00-21:00)", "meaning": "代表黑社会、信仰、诈骗。"},
    {"name": "亥", "order": 12, "wuxing": "水", "shichen": "亥时(21:00-23:00)", "meaning": "代表憨直、助人为乐，亦主暗昧之地。"},
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
