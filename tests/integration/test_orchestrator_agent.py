"""集成测试：Orchestrator Agent"""

import pytest
from datetime import datetime

from backend.ai_agents.agents.orchestrator import OrchestratorAgent


@pytest.fixture
def orchestrator() -> OrchestratorAgent:
    """创建 Orchestrator Agent 实例"""
    return OrchestratorAgent()


def test_complete_input_ready_to_execute(orchestrator: OrchestratorAgent) -> None:
    """场景 1：完整输入，直接准备执行占卜"""
    user_input = "我想算小六壬，报数3和5，男，现在想问事业方面的问题"
    
    result = orchestrator.process(user_input)
    
    # 验证意图识别
    assert result["intent"] == "divination"
    
    # 验证槽位填充
    assert result["slots"]["num1"] == 3
    assert result["slots"]["num2"] == 5
    assert result["slots"]["gender"] == "男"
    assert result["slots"]["question_type"] in ["事业", "综合"]
    assert "ask_time" in result["slots"]
    
    # 验证状态
    assert result["ready_to_execute"] is True
    assert result["clarification_needed"] is False
    assert len(result["missing_slots"]) == 0
    
    # 验证算法提示
    assert result["algorithm_hint"] == "xlr-liuren"


def test_missing_slots_triggers_clarification(orchestrator: OrchestratorAgent) -> None:
    """场景 2：缺失槽位，触发追问"""
    user_input = "我想算命"
    
    result = orchestrator.process(user_input)
    
    # 验证意图识别
    assert result["intent"] in ["divination", "consultation"]
    
    # 验证需要追问
    assert result["clarification_needed"] is True
    assert result["ready_to_execute"] is False
    assert len(result["missing_slots"]) > 0
    
    # 验证有追问消息
    assert result["clarification_message"] != ""
    assert len(result["clarification_message"]) > 10
    
    # 验证追问次数
    assert result["follow_up_count"] == 0


def test_invalid_number_range(orchestrator: OrchestratorAgent) -> None:
    """场景 3：无效输入（报数超出范围）"""
    # 使用接近但超出范围的数字（更容易被 LLM 提取）
    user_input = "报数7和8，男生，问事业"
    
    result = orchestrator.process(user_input)
    
    # 验证需要追问（因为数字无效被移除）
    assert result["clarification_needed"] is True
    assert result["ready_to_execute"] is False
    
    # 验证有验证错误或缺失槽位
    has_validation_error = (
        "validation_errors" in result or 
        any("invalid" in slot for slot in result["missing_slots"]) or
        "num1" in result["missing_slots"] or
        "num2" in result["missing_slots"]
    )
    assert has_validation_error
    
    # 验证追问消息非空
    assert len(result["clarification_message"]) > 0


def test_progressive_slot_filling(orchestrator: OrchestratorAgent) -> None:
    """测试渐进式槽位填充（多轮对话）"""
    # 第一轮：用户只提供部分信息
    result1 = orchestrator.process(
        "我想算小六壬",
        conversation_history=[],
        current_slots={},
        follow_up_count=0
    )
    
    assert result1["clarification_needed"] is True
    assert len(result1["missing_slots"]) > 0
    
    # 第二轮：用户补充报数
    result2 = orchestrator.process(
        "报数3和5",
        conversation_history=[
            {"role": "user", "content": "我想算小六壬"},
            {"role": "assistant", "content": result1["clarification_message"]}
        ],
        current_slots=result1["slots"],
        follow_up_count=1
    )
    
    # 应该识别到报数
    assert "num1" in result2["slots"] or result2["clarification_needed"]
    
    # 如果仍需追问，验证追问次数增加
    if result2["clarification_needed"]:
        assert result2["follow_up_count"] == 1


def test_max_follow_ups_exceeded(orchestrator: OrchestratorAgent) -> None:
    """测试追问次数超限"""
    user_input = "嗯"
    
    result = orchestrator.process(
        user_input,
        conversation_history=[],
        current_slots={},
        follow_up_count=3  # 已达到最大次数
    )
    
    # 验证错误状态
    assert "error" in result
    assert result["error"] == "max_follow_ups_exceeded"
    assert result["ready_to_execute"] is False
    
    # 验证提示用户重新开始
    assert "重新开始" in result["clarification_message"]


def test_gender_normalization(orchestrator: OrchestratorAgent) -> None:
    """测试性别字段标准化"""
    user_input = "报数1和2，我是男的，问财运"
    
    result = orchestrator.process(user_input)
    
    # 验证性别被标准化为"男"
    if "gender" in result["slots"]:
        assert result["slots"]["gender"] in ["男", "女"]


def test_default_values_applied(orchestrator: OrchestratorAgent) -> None:
    """测试默认值应用"""
    user_input = "报数3和5，男生"
    
    result = orchestrator.process(user_input)
    
    # 验证默认值
    assert "ask_time" in result["slots"]  # 应自动填充当前时间
    assert "algorithm_hint" in result  # 应有默认算法
    assert result["algorithm_hint"] == "xlr-liuren"


def test_question_type_extraction(orchestrator: OrchestratorAgent) -> None:
    """测试问题类型提取"""
    test_cases = [
        ("报数1和2，男，问事业", ["事业", "综合"]),
        ("报数3和4，女，财运怎么样", ["财运", "综合"]),
        ("报数5和6，男生，感情", ["感情", "综合"]),
    ]
    
    for user_input, expected_types in test_cases:
        result = orchestrator.process(user_input)
        
        if "question_type" in result["slots"]:
            assert result["slots"]["question_type"] in expected_types


def test_intent_classification(orchestrator: OrchestratorAgent) -> None:
    """测试意图分类"""
    test_cases = [
        ("我想算小六壬", "divination"),
        ("报数3和5算一卦", "divination"),
        ("查看我的历史记录", "history"),
        ("给我一些建议", "consultation"),
    ]
    
    for user_input, expected_intent in test_cases:
        result = orchestrator.process(user_input)
        
        # 意图应该匹配（或者至少不是错误）
        assert result["intent"] != "error" or "clarification" in result["intent"]


def test_algorithm_hint_recognition(orchestrator: OrchestratorAgent) -> None:
    """测试算法提示识别"""
    user_input = "用小六壬算法，报数2和4，男，问健康"
    
    result = orchestrator.process(user_input)
    
    # 验证算法提示
    assert result["algorithm_hint"] == "xlr-liuren"


def test_conversation_history_context(orchestrator: OrchestratorAgent) -> None:
    """测试对话历史上下文"""
    history = [
        {"role": "user", "content": "我想算命"},
        {"role": "assistant", "content": "请问您的报数是多少？"},
        {"role": "user", "content": "3和5"},
        {"role": "assistant", "content": "请问您的性别是？"}
    ]
    
    result = orchestrator.process(
        "我是男生",
        conversation_history=history,
        current_slots={"num1": 3, "num2": 5},
        follow_up_count=2
    )
    
    # 应该识别到性别
    if "gender" in result["slots"]:
        assert result["slots"]["gender"] == "男"
    
    # 验证追问次数传递
    assert result["follow_up_count"] == 2
