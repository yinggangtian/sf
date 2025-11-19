# pyright: reportMissingImports=false
"""小六壬算法核心逻辑的单元测试。"""

from __future__ import annotations

from datetime import datetime
import importlib

pytest = importlib.import_module("pytest")

from backend.ai_agents.xlr.adapters.liuren_adapter import LiurenAdapter
from backend.ai_agents.xlr.liuren.utils import KnowledgeBase
from backend.shared.db.models.knowledge import DiZhi, Gong, Qin, Shou


@pytest.fixture(name="knowledge_base")
def knowledge_base_fixture() -> KnowledgeBase:
    """构造一个包含基础数据的内存版知识库。"""

    kb = KnowledgeBase()

    kb.load_gong_data(
        [
            Gong(name="大安", position=1, wuxing="木", meaning="安定", attributes={}),
            Gong(name="留连", position=2, wuxing="水", meaning="反复", attributes={}),
            Gong(name="速喜", position=3, wuxing="金", meaning="喜讯", attributes={}),
            Gong(name="赤口", position=4, wuxing="火", meaning="口舌", attributes={}),
            Gong(name="小吉", position=5, wuxing="木", meaning="小吉", attributes={}),
            Gong(name="空亡", position=6, wuxing="土", meaning="阻滞", attributes={}),
        ]
    )

    kb.load_shou_data(
        [
            Shou(name="青龙", position=1, wuxing="木", characteristics="吉庆", meaning="得助", attributes={}),
            Shou(name="朱雀", position=2, wuxing="火", characteristics="表达", meaning="口舌", attributes={}),
            Shou(name="勾陈", position=3, wuxing="土", characteristics="守成", meaning="稳重", attributes={}),
            Shou(name="腾蛇", position=4, wuxing="火", characteristics="灵动", meaning="变化", attributes={}),
            Shou(name="白虎", position=5, wuxing="金", characteristics="果断", meaning="谨慎", attributes={}),
            Shou(name="玄武", position=6, wuxing="水", characteristics="谋略", meaning="隐藏", attributes={}),
        ]
    )

    kb.load_qin_data(
        [
            Qin(name="父母", relationship="长辈", meaning="支持", usage_context=None, attributes={}),
            Qin(name="官鬼", relationship="职责", meaning="压力", usage_context=None, attributes={}),
        ]
    )

    kb.load_dizhi_data(
        [
            DiZhi(name="子", order=1, wuxing="水", shichen="子时", meaning=""),
            DiZhi(name="丑", order=2, wuxing="土", shichen="丑时", meaning=""),
            DiZhi(name="寅", order=3, wuxing="木", shichen="寅时", meaning=""),
            DiZhi(name="卯", order=4, wuxing="木", shichen="卯时", meaning=""),
            DiZhi(name="辰", order=5, wuxing="土", shichen="辰时", meaning=""),
            DiZhi(name="巳", order=6, wuxing="火", shichen="巳时", meaning=""),
            DiZhi(name="午", order=7, wuxing="火", shichen="午时", meaning=""),
            DiZhi(name="未", order=8, wuxing="土", shichen="未时", meaning=""),
            DiZhi(name="申", order=9, wuxing="金", shichen="申时", meaning=""),
            DiZhi(name="酉", order=10, wuxing="金", shichen="酉时", meaning=""),
            DiZhi(name="戌", order=11, wuxing="土", shichen="戌时", meaning=""),
            DiZhi(name="亥", order=12, wuxing="水", shichen="亥时", meaning=""),
        ]
    )

    kb.load_wuxing_relations(
        {
            "木": {"火": "生", "土": "克", "金": "克我", "水": "生我"},
            "火": {"土": "生", "金": "克", "水": "克我", "木": "生我"},
            "土": {"金": "生", "水": "克", "木": "克我", "火": "生我"},
            "金": {"水": "生", "木": "克", "火": "克我", "土": "生我"},
            "水": {"木": "生", "火": "克", "土": "克我", "金": "生我"},
        }
    )

    return kb


@pytest.fixture(name="liuren_adapter")
def liuren_adapter_fixture(knowledge_base: KnowledgeBase) -> LiurenAdapter:
    """提供已经装载知识库的数据适配器。"""
    return LiurenAdapter(knowledge_base)


def _run_qigua(adapter: LiurenAdapter) -> dict:
    """帮助函数：执行一次标准起卦并返回结果。"""
    return adapter.run(
        {
            "operation": "qigua",
            "number1": 3,
            "number2": 5,
            "qigua_time": datetime(2024, 5, 10, 10, 0, 0),
        }
    )


def test_qigua_generates_expected_paipan(liuren_adapter: LiurenAdapter) -> None:
    """验证起卦输出的落宫、时辰和六宫六兽排盘。"""
    result = _run_qigua(liuren_adapter)

    assert result["success"] is True
    assert result["luogong"] == 1
    assert result["shichen"] == "巳"

    paipan = result["paipan_result"]
    liugong = paipan["paipan_data"]["liugong"]
    liushou = paipan["paipan_data"]["liushou"]

    assert liugong["gong_1"]["is_luogong"] is True
    assert len(liushou) == 6
    assert paipan["qigua_info"]["number1"] == 3
    assert paipan["qigua_info"]["number2"] == 5


def test_jiegua_returns_expected_yongshen(liuren_adapter: LiurenAdapter) -> None:
    """验证解卦阶段的用神选择及综合解读文本。"""
    paipan_result = _run_qigua(liuren_adapter)["paipan_result"]

    result = liuren_adapter.run(
        {
            "operation": "jiegua",
            "paipan_result": paipan_result,
            "question_type": "事业",
            "gender": "男",
        }
    )

    assert result["success"] is True
    interpretation = result["interpretation_result"]
    assert interpretation["yongshen"] == ["官鬼", "父母"]
    assert "事业" in result["comprehensive_text"]
    assert interpretation["gong_analysis"]["luogong_analysis"]


def test_find_object_provides_direction_and_guidance(liuren_adapter: LiurenAdapter) -> None:
    """验证寻物分析包含方向、时间估计等信息。"""
    paipan_result = _run_qigua(liuren_adapter)["paipan_result"]

    result = liuren_adapter.run(
        {
            "operation": "find_object",
            "paipan_result": paipan_result,
            "item_description": "钱包",
        }
    )

    assert result["success"] is True

    find_result = result["find_object_result"]
    assert find_result["direction_analysis"]["primary_direction"]
    assert find_result["time_estimation"]["period"]
    assert 0.0 <= find_result["success_probability"] <= 1.0
    assert "钱包" in result["item_description"]


def test_qigua_rejects_invalid_numbers(liuren_adapter: LiurenAdapter) -> None:
    """报数超出合法范围时必须抛出错误。"""
    with pytest.raises(ValueError):
        liuren_adapter.run({"operation": "qigua", "number1": 0, "number2": 3})


def test_qigua_invalid_time_format_raises(liuren_adapter: LiurenAdapter) -> None:
    """非法时间字符串会在执行阶段触发运行时错误。"""
    with pytest.raises(RuntimeError):
        liuren_adapter.run(
            {
                "operation": "qigua",
                "number1": 2,
                "number2": 4,
                "qigua_time": "not-an-iso-time",
            }
        )


def test_invalid_operation_type(liuren_adapter: LiurenAdapter) -> None:
    """不支持的操作类型需要显式报错。"""
    with pytest.raises(ValueError):
        liuren_adapter.run({"operation": "unknown"})
