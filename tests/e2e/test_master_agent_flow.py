"""E2E tests for MasterAgent flow
测试完整的 Orchestrator → Tool → Explainer 流程
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.ai_agents.agents.master_agent import MasterAgent
from backend.ai_agents.agents.orchestrator import OrchestratorAgent
from backend.ai_agents.agents.explainer import ExplainerAgent


@pytest.fixture
def mock_orchestrator():
    """Mock Orchestrator Agent"""
    orchestrator = Mock(spec=OrchestratorAgent)
    return orchestrator


@pytest.fixture
def mock_explainer():
    """Mock Explainer Agent"""
    with patch("backend.ai_agents.agents.master_agent.ExplainerAgent") as MockExplainer:
        explainer = Mock()
        explainer.generate_explanation.return_value = "这是一个详细的占卜解释，包含宫位分析和用神解读。"
        MockExplainer.return_value = explainer
        yield explainer


@pytest.fixture
def mock_services():
    """Mock all services"""
    divination_service = Mock()
    divination_service.interpretation_service = Mock()
    
    rag_service = Mock()
    memory_service = Mock()
    
    return {
        "divination": divination_service,
        "rag": rag_service,
        "memory": memory_service
    }


@pytest.fixture
def mock_liuren_tool():
    """Mock LiurenTool"""
    with patch("backend.ai_agents.agents.master_agent.LiurenTool") as MockTool:
        tool = Mock()
        tool.qigua_and_jiegua.return_value = {
            "success": True,
            "qigua": {
                "luogong": 3,
                "luogong_name": "坎宫",
                "shichen": "巳",
                "paipan_summary": "落宫为坎宫，时辰为巳时"
            },
            "jiegua": {
                "yongshen": "青龙",
                "interpretation": "青龙主文书喜事，坎宫属水，利于智慧谋划。",
                "favorable": True,
                "suggestions": ["保持冷静", "顺势而为"]
            }
        }
        MockTool.return_value = tool
        yield tool


@pytest.fixture
def mock_rag_tool():
    """Mock RAGTool"""
    with patch("backend.ai_agents.agents.master_agent.RAGTool") as MockTool:
        tool = Mock()
        tool.search.return_value = {
            "success": True,
            "chunks": [
                {
                    "chunk_text": "青龙为六兽之首，主文书、财帛、喜庆之事。",
                    "metadata": {"source": "六壬神煞解析"},
                    "score": 0.95
                }
            ],
            "total_results": 1,
            "degraded": False
        }
        MockTool.return_value = tool
        yield tool


@pytest.fixture
def mock_profile_tool():
    """Mock ProfileTool"""
    with patch("backend.ai_agents.agents.master_agent.ProfileTool") as MockTool:
        tool = Mock()
        tool.get_profile.return_value = {
            "success": True,
            "profile": {
                "user_id": 1,
                "gender": "男",
                "total_divinations": 5,
                "preferred_question_types": "事业"
            },
            "exists": True
        }
        MockTool.return_value = tool
        yield tool


@pytest.fixture
def mock_history_tool():
    """Mock HistoryTool"""
    with patch("backend.ai_agents.agents.master_agent.HistoryTool") as MockTool:
        tool = Mock()
        MockTool.return_value = tool
        yield tool


@pytest.fixture
def master_agent(
    mock_orchestrator,
    mock_explainer,
    mock_services,
    mock_liuren_tool,
    mock_rag_tool,
    mock_profile_tool,
    mock_history_tool
):
    """Create MasterAgent with all mocks"""
    agent = MasterAgent(
        orchestrator=mock_orchestrator,
        explainer=mock_explainer,
        divination_service=mock_services["divination"],
        rag_service=mock_services["rag"],
        memory_service=mock_services["memory"],
        tool_timeout=10.0
    )
    
    # 替换工具实例为 mock
    agent.liuren_tool = mock_liuren_tool
    agent.rag_tool = mock_rag_tool
    agent.profile_tool = mock_profile_tool
    agent.history_tool = mock_history_tool
    
    return agent


class TestMasterAgentFlow:
    """Test MasterAgent complete flow"""
    
    def test_complete_divination_flow(
        self,
        master_agent,
        mock_orchestrator,
        mock_liuren_tool,
        mock_rag_tool,
        mock_profile_tool,
        mock_explainer
    ):
        """测试完整占卜流程（Orchestrator → Tool → Explainer）"""
        # Mock Orchestrator 返回完整槽位
        mock_orchestrator.process.return_value = {
            "ready_to_execute": True,
            "clarification_needed": False,
            "intent": "divination",
            "slots": {
                "num1": 3,
                "num2": 5,
                "gender": "男",
                "question_type": "事业"
            }
        }
        
        # 执行
        result = master_agent.run(
            user_message="我想算事业运势，报数 3 和 5，男",
            user_id=1,
            session_id="test-session-001"
        )
        
        # 验证流程
        assert result["status"] == "success"
        assert "reply" in result
        assert result["reply"] == "这是一个详细的占卜解释，包含宫位分析和用神解读。"
        
        # 验证调用顺序
        mock_orchestrator.process.assert_called_once()
        mock_liuren_tool.qigua_and_jiegua.assert_called_once_with(
            number1=3,
            number2=5,
            question_type="事业",
            gender="男",
            user_id=1
        )
        mock_rag_tool.search.assert_called_once()
        mock_profile_tool.get_profile.assert_called_once_with(1)
        mock_explainer.generate_explanation.assert_called_once()
        
        # 验证 meta 信息
        assert "meta" in result
        assert result["meta"]["intent"] == "divination"
        assert result["meta"]["rag_used"] is True
        assert result["meta"]["profile_used"] is True
    
    def test_clarification_needed(
        self,
        master_agent,
        mock_orchestrator
    ):
        """测试需要追问的场景"""
        # Mock Orchestrator 返回缺失槽位
        mock_orchestrator.process.return_value = {
            "clarification_needed": True,
            "ready_to_execute": False,
            "clarification_message": "请问您想问什么类型的问题？（事业/财运/感情）",
            "missing_slots": ["question_type", "num1", "num2"]
        }
        
        # 执行
        result = master_agent.run(
            user_message="我想算命",
            user_id=1
        )
        
        # 验证返回追问
        assert result["status"] == "clarification_needed"
        assert "请问您想问什么类型的问题" in result["reply"]
        assert "missing_slots" in result
        assert "question_type" in result["missing_slots"]
    
    def test_tool_timeout(
        self,
        master_agent,
        mock_orchestrator,
        mock_liuren_tool
    ):
        """测试工具超时处理"""
        # Mock Orchestrator 返回完整槽位
        mock_orchestrator.process.return_value = {
            "ready_to_execute": True,
            "clarification_needed": False,
            "intent": "divination",
            "slots": {
                "num1": 3,
                "num2": 5,
                "gender": "男",
                "question_type": "事业"
            }
        }
        
        # Mock 工具超时
        from concurrent.futures import TimeoutError as FuturesTimeoutError
        mock_liuren_tool.qigua_and_jiegua.side_effect = FuturesTimeoutError()
        
        # 执行
        result = master_agent.run(
            user_message="我想算事业",
            user_id=1
        )
        
        # 验证降级处理
        assert result["status"] == "tool_error"
        assert "抱歉" in result["reply"]
    
    def test_tool_failure(
        self,
        master_agent,
        mock_orchestrator,
        mock_liuren_tool
    ):
        """测试工具调用失败"""
        # Mock Orchestrator 返回完整槽位
        mock_orchestrator.process.return_value = {
            "ready_to_execute": True,
            "clarification_needed": False,
            "intent": "divination",
            "slots": {
                "num1": 3,
                "num2": 5,
                "gender": "男",
                "question_type": "事业"
            }
        }
        
        # Mock 工具失败
        mock_liuren_tool.qigua_and_jiegua.return_value = {
            "success": False,
            "error": "数据库连接失败"
        }
        
        # 执行
        result = master_agent.run(
            user_message="我想算事业",
            user_id=1
        )
        
        # 验证错误处理
        assert result["status"] == "tool_error"
        assert "抱歉" in result["reply"]
    
    def test_rag_degradation(
        self,
        master_agent,
        mock_orchestrator,
        mock_liuren_tool,
        mock_rag_tool,
        mock_explainer
    ):
        """测试 RAG 降级（不影响主流程）"""
        # Mock Orchestrator 返回完整槽位
        mock_orchestrator.process.return_value = {
            "ready_to_execute": True,
            "clarification_needed": False,
            "intent": "divination",
            "slots": {
                "num1": 3,
                "num2": 5,
                "gender": "男",
                "question_type": "事业"
            }
        }
        
        # Mock RAG 失败
        mock_rag_tool.search.return_value = {
            "success": False,
            "chunks": [],
            "error": "检索超时"
        }
        
        # 执行
        result = master_agent.run(
            user_message="我想算事业",
            user_id=1
        )
        
        # 验证仍能成功（RAG 失败不影响主流程）
        assert result["status"] == "success"
        assert "reply" in result
        
        # 验证 Explainer 被调用（rag_chunks 为 None）
        mock_explainer.generate_explanation.assert_called_once()
        call_args = mock_explainer.generate_explanation.call_args
        assert call_args.kwargs.get("rag_chunks") is None
    
    def test_profile_degradation(
        self,
        master_agent,
        mock_orchestrator,
        mock_liuren_tool,
        mock_profile_tool,
        mock_explainer
    ):
        """测试用户画像降级（不影响主流程）"""
        # Mock Orchestrator 返回完整槽位
        mock_orchestrator.process.return_value = {
            "ready_to_execute": True,
            "clarification_needed": False,
            "intent": "divination",
            "slots": {
                "num1": 3,
                "num2": 5,
                "gender": "男",
                "question_type": "事业"
            }
        }
        
        # Mock Profile 失败
        mock_profile_tool.get_profile.return_value = {
            "success": False,
            "error": "用户不存在"
        }
        
        # 执行
        result = master_agent.run(
            user_message="我想算事业",
            user_id=1
        )
        
        # 验证仍能成功
        assert result["status"] == "success"
        
        # 验证 Explainer 被调用（user_profile 为 None）
        mock_explainer.generate_explanation.assert_called_once()
        call_args = mock_explainer.generate_explanation.call_args
        assert call_args.kwargs.get("user_profile") is None
    
    def test_unsupported_intent(
        self,
        master_agent,
        mock_orchestrator
    ):
        """测试不支持的意图"""
        # Mock Orchestrator 返回不支持的意图
        mock_orchestrator.process.return_value = {
            "ready_to_execute": True,
            "clarification_needed": False,
            "intent": "history",  # 暂不支持
            "slots": {}
        }
        
        # 执行
        result = master_agent.run(
            user_message="查看我的历史记录",
            user_id=1
        )
        
        # 验证返回不支持提示
        assert result["status"] == "unsupported_intent"
        assert "暂不支持" in result["reply"]
    
    def test_orchestrator_error(
        self,
        master_agent,
        mock_orchestrator
    ):
        """测试 Orchestrator 返回错误"""
        # Mock Orchestrator 返回错误
        mock_orchestrator.process.return_value = {
            "status": "error",
            "error_message": "无法解析用户输入"
        }
        
        # 执行
        result = master_agent.run(
            user_message="@#$%^&*",
            user_id=1
        )
        
        # 验证错误处理
        assert result["status"] == "error"
        assert "无法解析" in result["reply"] or "无法理解" in result["reply"]
    
    def test_exception_handling(
        self,
        master_agent,
        mock_orchestrator
    ):
        """测试异常处理"""
        # Mock Orchestrator 抛出异常
        mock_orchestrator.process.side_effect = Exception("Unexpected error")
        
        # 执行
        result = master_agent.run(
            user_message="测试消息",
            user_id=1
        )
        
        # 验证异常被捕获
        assert result["status"] == "error"
        assert "系统处理出错" in result["reply"]
        assert "error" in result
