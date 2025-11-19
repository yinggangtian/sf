"""
端到端测试：FastAPI 路由层
测试占卜接口和历史查询接口的完整流程
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.main import app
from app.dependencies import get_db, get_master_agent, get_divination_service
from backend.shared.db.models.knowledge import Gong, Shou, Qin, DiZhi


@pytest.fixture(name="mock_db_session")
def mock_db_session_fixture():
    """Mock 数据库会话"""
    mock_session = Mock(spec=Session)
    
    # Mock 知识库数据查询
    mock_gong = Mock(spec=Gong)
    mock_gong.position = 1
    mock_gong.name = "大安"
    
    mock_shou = Mock(spec=Shou)
    mock_shou.position = 1
    mock_shou.name = "青龙"
    
    mock_qin = Mock(spec=Qin)
    mock_qin.name = "父母"
    
    mock_dizhi = Mock(spec=DiZhi)
    mock_dizhi.name = "子"
    
    # 配置查询返回值
    mock_query = Mock()
    mock_query.order_by.return_value.all.return_value = [mock_gong]
    mock_query.all.return_value = [mock_dizhi]
    
    def query_side_effect(model):
        if model == Gong:
            result = Mock()
            result.order_by.return_value.all.return_value = [mock_gong] * 6
            return result
        elif model == Shou:
            result = Mock()
            result.order_by.return_value.all.return_value = [mock_shou] * 6
            return result
        elif model == Qin:
            result = Mock()
            result.all.return_value = [mock_qin] * 6
            return result
        elif model == DiZhi:
            result = Mock()
            result.all.return_value = [mock_dizhi] * 12
            return result
        return mock_query
    
    mock_session.query.side_effect = query_side_effect
    
    return mock_session


@pytest.fixture(name="mock_master_agent")
def mock_master_agent_fixture():
    """Mock MasterAgent"""
    mock_agent = Mock()
    mock_agent.run.return_value = {
        "reply": "根据您的占卜，此卦落于坎宫，青龙当值...",
        "status": "success",
        "divination_result": {
            "qigua": {
                "luogong": "坎宫",
                "luogong_position": 1,
                "yongshen": "青龙",
                "yongshen_position": 1
            },
            "jiegua": {
                "favorable": True,
                "analysis": "青龙主吉，事业顺利"
            }
        },
        "meta": {
            "processing_time": 2.5,
            "rag_used": True,
            "profile_used": True
        }
    }
    return mock_agent


def test_health_check():
    """测试健康检查接口"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_ai_health_check():
    """测试 AI 模块健康检查"""
    client = TestClient(app)
    response = client.get("/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AI Agent API"


def test_divination_endpoint_complete_flow(
    mock_db_session,
    mock_master_agent
):
    """
    测试占卜接口 - 完整流程
    
    场景：用户发送完整占卜请求 → MasterAgent 处理 → 返回结构化结果
    """
    # 覆盖依赖注入
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_master_agent] = lambda: mock_master_agent
    
    try:
        # 创建测试客户端
        client = TestClient(app)
        
        # 发送请求
        request_data = {
            "message": "我想算事业运势，报数 3 和 5，男",
            "user_id": 1,
            "session_id": "session-001"
        }
        
        response = client.post("/ai/divination", json=request_data)
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        
        assert "reply" in data
        assert "status" in data
        assert data["status"] == "success"
        assert "divination_result" in data
        assert "meta" in data
        
        # 验证 MasterAgent 被正确调用
        mock_master_agent.run.assert_called_once()
        call_kwargs = mock_master_agent.run.call_args.kwargs
        assert call_kwargs["user_message"] == request_data["message"]
        assert call_kwargs["user_id"] == request_data["user_id"]
        assert call_kwargs["session_id"] == request_data["session_id"]
    finally:
        # 清理依赖覆盖
        app.dependency_overrides.clear()


def test_divination_endpoint_clarification_needed(
    mock_db_session
):
    """
    测试占卜接口 - 需要追问
    
    场景：用户输入不完整 → 返回追问提示
    """
    # 创建 mock agent
    mock_agent = Mock()
    mock_agent.run.return_value = {
        "reply": "请告诉我两个 1-6 之间的数字",
        "status": "clarification_needed",
        "divination_result": None,
        "meta": {"missing_slots": ["num1", "num2"]}
    }
    
    # 覆盖依赖注入
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_master_agent] = lambda: mock_agent
    
    try:
        # 创建测试客户端
        client = TestClient(app)
        
        # 发送请求
        request_data = {
            "message": "我想算命",
            "user_id": 1
        }
        
        response = client.post("/ai/divination", json=request_data)
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "clarification_needed"
        assert "请告诉我" in data["reply"]
        assert data["divination_result"] is None
    finally:
        app.dependency_overrides.clear()


def test_divination_endpoint_error_handling(
    mock_db_session
):
    """
    测试占卜接口 - 错误处理
    
    场景：MasterAgent 抛出异常 → 返回 500 错误
    """
    # 创建 mock agent
    mock_agent = Mock()
    mock_agent.run.side_effect = Exception("内部错误")
    
    # 覆盖依赖注入
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_master_agent] = lambda: mock_agent
    
    try:
        # 创建测试客户端
        client = TestClient(app)
        
        # 发送请求
        request_data = {
            "message": "测试错误",
            "user_id": 1
        }
        
        response = client.post("/ai/divination", json=request_data)
        
        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "服务器处理错误" in data["detail"]
    finally:
        app.dependency_overrides.clear()


def test_divination_endpoint_invalid_request():
    """
    测试占卜接口 - 无效请求
    
    场景：缺少必填字段 → 返回 422 错误
    """
    # 创建测试客户端
    client = TestClient(app)
    
    # 缺少 user_id
    request_data = {
        "message": "测试"
    }
    
    response = client.post("/ai/divination", json=request_data)
    
    # 验证响应
    assert response.status_code == 422


def test_history_endpoint(
    mock_db_session
):
    """
    测试历史查询接口
    
    场景：查询用户历史记录 → 返回分页结果
    """
    # 创建 mock service
    mock_service = Mock()
    mock_service.get_statistics.return_value = {
        "total_divinations": 15,
        "common_questions": ["事业", "感情"]
    }
    
    # 覆盖依赖注入
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_divination_service] = lambda: mock_service
    
    try:
        # 创建测试客户端
        client = TestClient(app)
        
        # 发送请求
        response = client.get("/ai/history/1?page=1&page_size=10")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        
        assert data["total"] == 15
        assert data["page"] == 1
        assert data["page_size"] == 10
    finally:
        app.dependency_overrides.clear()


def test_history_endpoint_invalid_page():
    """
    测试历史查询接口 - 无效页码
    
    场景：页码小于 1 → 返回 400 错误
    """
    # 创建测试客户端
    client = TestClient(app)
    
    # 发送请求
    response = client.get("/ai/history/1?page=0")
    
    # 验证响应
    assert response.status_code == 400
    data = response.json()
    assert "页码必须大于等于 1" in data["detail"]


def test_history_endpoint_invalid_page_size():
    """
    测试历史查询接口 - 无效每页大小
    
    场景：每页大小超过 50 → 返回 400 错误
    """
    # 创建测试客户端
    client = TestClient(app)
    
    # 发送请求
    response = client.get("/ai/history/1?page=1&page_size=100")
    
    # 验证响应
    assert response.status_code == 400
    data = response.json()
    assert "每页大小必须在 1-50 之间" in data["detail"]


def test_history_endpoint_user_not_found(
    mock_db_session
):
    """
    测试历史查询接口 - 用户不存在
    
    场景：查询不存在的用户 → 返回 404 错误
    """
    # 创建 mock service
    mock_service = Mock()
    mock_service.get_statistics.side_effect = ValueError("用户不存在")
    
    # 覆盖依赖注入
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_divination_service] = lambda: mock_service
    
    try:
        # 创建测试客户端
        client = TestClient(app)
        
        # 发送请求
        response = client.get("/ai/history/999?page=1&page_size=10")
        
        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "用户不存在" in data["detail"]
    finally:
        app.dependency_overrides.clear()
