"""Integration tests for ExplainerAgent"""

import pytest
from unittest.mock import Mock, patch
from backend.ai_agents.agents.explainer import ExplainerAgent


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch("backend.ai_agents.agents.explainer.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        
        mock_message.content = """根据您的占卜，此卦落于坎宫，坎为水，属水象，象征着智慧与流动。从时辰来看，您在巳时问卜，此时阳气正盛，是思考与决策的好时机。

从六宫排盘来看，大安宫位于第一宫，代表基础稳固；留连宫位于第四宫，提示您可能需要耐心等待；速喜宫位于第六宫，预示着最终会有好消息传来。

您的用神为青龙，青龙主文书、喜庆之事，这表明您所问之事具有较大的成功概率。从宫位关系来看，各宫之间呈现出和谐的生克关系。

综合来看，您可能会遇到一些小的波折，但整体趋势是向好的。建议您保持耐心，顺其自然，不要过于急躁。"""
        
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        
        yield mock_client


@pytest.fixture
def sample_divination_result():
    """Sample divination result"""
    return {
        "paipan_result": {
            "ask_time": "2024-01-15 10:30:00",
            "gender": "男",
            "num1": 3,
            "num2": 5,
            "luogong": "坎宫",
            "luogong_wuxing": "水",
            "shichen": "巳时",
            "shichen_dizhi": "巳",
            "liugong_paipan": [
                {"position": 1, "name": "大安", "wuxing": "木"},
                {"position": 2, "name": "留连", "wuxing": "土"},
                {"position": 3, "name": "速喜", "wuxing": "火"}
            ],
            "liushou_paipan": [
                {"position": 1, "name": "青龙"},
                {"position": 2, "name": "朱雀"},
                {"position": 3, "name": "勾陈"}
            ]
        },
        "interpretation_result": {
            "yongshen": "青龙",
            "yongshen_analysis": "青龙主文书、喜事",
            "gong_relations": {
                "生克关系": "坎水生木，木生火",
                "强弱分析": "水旺木相"
            },
            "comprehensive_interpretation": "卦象整体向好"
        }
    }


@pytest.fixture
def sample_rag_chunks():
    """Sample RAG chunks"""
    return [
        {
            "chunk_text": "青龙为吉兽，主文书、财帛、喜庆之事。",
            "metadata": {"source": "六壬神煞解析", "chapter": "六兽篇"}
        },
        {
            "chunk_text": "坎宫属水，主智慧、流动、变化。",
            "metadata": {"source": "六壬宫位详解", "chapter": "八宫篇"}
        }
    ]


@pytest.fixture
def sample_user_profile():
    """Sample user profile"""
    return {
        "gender": "男",
        "total_divinations": 12,
        "preferred_question_types": "事业、财运"
    }


class TestExplainerAgent:
    """Test ExplainerAgent"""
    
    def test_initialization(self, mock_openai_client):
        """测试 Agent 初始化"""
        agent = ExplainerAgent()
        
        # 验证 system prompt 已加载
        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0
        assert "解释生成器" in agent.system_prompt or "六壬" in agent.system_prompt
        
        # 验证模板已加载
        assert agent.template is not None
        assert len(agent.template) > 0
        assert "{question}" in agent.template
        assert "{luogong}" in agent.template
    
    def test_basic_explanation_without_rag(
        self,
        mock_openai_client,
        sample_divination_result
    ):
        """测试基础解释生成（不带 RAG）"""
        agent = ExplainerAgent()
        
        explanation = agent.generate_explanation(
            divination_result=sample_divination_result,
            question="最近事业运势如何？",
            question_type="事业"
        )
        
        # 验证返回了内容
        assert explanation is not None
        assert len(explanation) > 0
        
        # 验证包含关键要素
        assert "坎宫" in explanation or "坎" in explanation
        assert "青龙" in explanation
        
        # 验证包含免责声明
        assert "温馨提示" in explanation or "仅供参考" in explanation
        
        # 验证 LLM 被调用
        mock_openai_client.chat.completions.create.assert_called_once()
        
        # 验证调用参数
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        
        # 验证 user message 包含必要信息
        user_message = messages[1]["content"]
        assert "最近事业运势如何" in user_message
        assert "坎宫" in user_message
        assert "青龙" in user_message
    
    def test_rag_enhanced_explanation(
        self,
        mock_openai_client,
        sample_divination_result,
        sample_rag_chunks
    ):
        """测试 RAG 增强的解释生成"""
        agent = ExplainerAgent()
        
        explanation = agent.generate_explanation(
            divination_result=sample_divination_result,
            question="财运如何？",
            question_type="财运",
            rag_chunks=sample_rag_chunks
        )
        
        # 验证返回了内容
        assert explanation is not None
        assert len(explanation) > 0
        
        # 验证 LLM 被调用
        mock_openai_client.chat.completions.create.assert_called_once()
        
        # 验证 prompt 中包含 RAG 内容
        call_args = mock_openai_client.chat.completions.create.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        
        # 检查 RAG chunk 的关键内容是否在 prompt 中
        assert "青龙为吉兽" in user_message or "六壬神煞解析" in user_message
        assert "坎宫属水" in user_message or "六壬宫位详解" in user_message
    
    def test_user_profile_integration(
        self,
        mock_openai_client,
        sample_divination_result,
        sample_user_profile
    ):
        """测试用户画像集成"""
        agent = ExplainerAgent()
        
        explanation = agent.generate_explanation(
            divination_result=sample_divination_result,
            question="今年运势",
            question_type="综合",
            user_profile=sample_user_profile
        )
        
        # 验证返回了内容
        assert explanation is not None
        
        # 验证 prompt 中包含用户画像信息
        call_args = mock_openai_client.chat.completions.create.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        
        # 检查用户画像关键信息
        assert "男" in user_message or "性别" in user_message
        assert "12" in user_message or "历史占卜次数" in user_message
    
    def test_guardrails_filtering(self, mock_openai_client, sample_divination_result):
        """测试 Guardrails 过滤（替换绝对化措辞）"""
        # Mock LLM 返回包含绝对化措辞的内容
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "您一定会成功，这是必然的结果，绝对不会失败。"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        agent = ExplainerAgent()
        
        explanation = agent.generate_explanation(
            divination_result=sample_divination_result,
            question="考试能过吗？",
            question_type="考试"
        )
        
        # 验证绝对化措辞被替换
        assert "一定会" not in explanation
        assert "必然" not in explanation
        assert "绝对" not in explanation
        
        # 验证替换后的措辞存在
        assert "大概率" in explanation or "很可能" in explanation or "有较大可能" in explanation
        
        # 验证免责声明存在
        assert "温馨提示" in explanation or "仅供参考" in explanation
    
    def test_disclaimer_appended(self, mock_openai_client, sample_divination_result):
        """测试免责声明自动添加"""
        agent = ExplainerAgent()
        
        explanation = agent.generate_explanation(
            divination_result=sample_divination_result,
            question="测试问题",
            question_type="综合"
        )
        
        # 验证免责声明在末尾
        assert "温馨提示" in explanation
        assert "仅供参考" in explanation or "娱乐" in explanation
    
    def test_fallback_on_llm_error(self, mock_openai_client, sample_divination_result):
        """测试 LLM 调用失败时的降级处理"""
        # Mock LLM 调用抛出异常
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        agent = ExplainerAgent()
        
        explanation = agent.generate_explanation(
            divination_result=sample_divination_result,
            question="测试问题",
            question_type="综合"
        )
        
        # 验证返回了降级解释
        assert explanation is not None
        assert len(explanation) > 0
        
        # 验证包含基本信息
        assert "坎宫" in explanation
        assert "青龙" in explanation
        
        # 验证包含降级提示
        assert "系统繁忙" in explanation or "暂时无法" in explanation or "稍后重试" in explanation
    
    def test_empty_divination_result(self, mock_openai_client):
        """测试空的占卜结果"""
        agent = ExplainerAgent()
        
        explanation = agent.generate_explanation(
            divination_result={},
            question="测试问题",
            question_type="综合"
        )
        
        # 验证仍能返回内容（使用默认值）
        assert explanation is not None
        assert len(explanation) > 0
    
    def test_template_variable_substitution(
        self,
        mock_openai_client,
        sample_divination_result
    ):
        """测试模板变量替换正确性"""
        agent = ExplainerAgent()
        
        agent.generate_explanation(
            divination_result=sample_divination_result,
            question="我的问题",
            question_type="财运"
        )
        
        # 获取实际发送给 LLM 的 prompt
        call_args = mock_openai_client.chat.completions.create.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        
        # 验证关键变量已被替换
        assert "我的问题" in user_message
        assert "财运" in user_message
        assert "坎宫" in user_message
        assert "青龙" in user_message
        assert "巳时" in user_message
        
        # 验证没有未替换的占位符
        assert "{question}" not in user_message
        assert "{luogong}" not in user_message
        assert "{yongshen}" not in user_message
