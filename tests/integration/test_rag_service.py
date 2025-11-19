"""集成测试：RAG Service 知识库检索服务"""

from __future__ import annotations

from typing import List
from unittest.mock import Mock, patch, MagicMock
import time

import importlib

pytest = importlib.import_module("pytest")

from backend.ai_agents.services.rag_service import RAGService
from backend.ai_agents.rag.retriever import Retriever
from backend.ai_agents.rag.schemas import SearchResult


@pytest.fixture(name="mock_retriever")
def mock_retriever_fixture() -> Mock:
    """创建模拟的检索器实例"""
    mock = Mock(spec=Retriever)
    
    # 默认返回模拟结果
    mock.search.return_value = [
        SearchResult(
            chunk_text="大安宫位主安定吉祥，五行属木，代表稳固和成长。",
            metadata={"source": "小六壬经典", "chapter": "六宫详解"},
            score=0.95
        ),
        SearchResult(
            chunk_text="留连宫位主事情拖延，需要耐心等待时机。",
            metadata={"source": "小六壬经典", "chapter": "六宫详解"},
            score=0.88
        ),
        SearchResult(
            chunk_text="速喜宫位主喜事将至，宜把握机会行动。",
            metadata={"source": "小六壬经典", "chapter": "六宫详解"},
            score=0.82
        ),
    ]
    
    mock.batch_search.return_value = {
        "大安": [
            SearchResult(
                chunk_text="大安宫位主安定吉祥。",
                metadata={"source": "小六壬经典"},
                score=0.95
            )
        ],
        "速喜": [
            SearchResult(
                chunk_text="速喜宫位主喜事将至。",
                metadata={"source": "小六壬经典"},
                score=0.90
            )
        ]
    }
    
    return mock


@pytest.fixture(name="rag_service")
def rag_service_fixture(mock_retriever: Mock) -> RAGService:
    """创建 RAG 服务实例（使用模拟检索器）"""
    return RAGService(retriever=mock_retriever)


def test_search_knowledge_single_keyword(rag_service: RAGService) -> None:
    """测试单关键词检索（使用模拟数据）"""
    response = rag_service.search_knowledge(
        keywords=["大安"],
        top_k=5,
        timeout=3.0
    )
    
    assert response.degraded is False
    assert response.total_count > 0
    assert len(response.results) > 0
    
    # 验证结果按 score 降序排列
    scores = [r.score for r in response.results]
    assert scores == sorted(scores, reverse=True)
    
    # 验证结果包含必需字段
    first_result = response.results[0]
    assert first_result.chunk_text
    assert first_result.metadata
    assert 0 <= first_result.score <= 1


def test_search_knowledge_multiple_keywords(rag_service: RAGService) -> None:
    """测试多关键词检索"""
    response = rag_service.search_knowledge(
        keywords=["大安", "吉祥", "稳定"],
        top_k=3,
        timeout=3.0
    )
    
    assert response.degraded is False
    assert len(response.results) <= 3


def test_search_knowledge_empty_keywords(rag_service: RAGService) -> None:
    """测试空关键词列表"""
    response = rag_service.search_knowledge(
        keywords=[],
        top_k=5,
        timeout=3.0
    )
    
    assert response.degraded is False
    assert response.total_count == 0
    assert len(response.results) == 0
    assert response.message == "未提供检索关键词"


def test_search_knowledge_top_k_limit(rag_service: RAGService) -> None:
    """测试 top_k 限制"""
    # 请求 2 个结果
    response = rag_service.search_knowledge(
        keywords=["小六壬"],
        top_k=2,
        timeout=3.0
    )
    
    assert len(response.results) <= 2


def test_search_knowledge_timeout_degradation() -> None:
    """测试超时降级（Mock 慢查询）"""
    # 创建一个会超时的 mock retriever
    mock_retriever = Mock(spec=Retriever)
    
    def slow_search(*args, **kwargs):
        time.sleep(5)  # 睡眠 5 秒，超过 timeout
        return []
    
    mock_retriever.search = slow_search
    
    service = RAGService(retriever=mock_retriever)
    
    response = service.search_knowledge(
        keywords=["测试"],
        top_k=5,
        timeout=1.0  # 设置 1 秒超时
    )
    
    # 验证超时后降级
    assert response.degraded is True
    assert response.total_count == 0
    assert len(response.results) == 0
    assert "超时" in (response.message or "")


def test_search_knowledge_exception_degradation() -> None:
    """测试异常降级"""
    # 创建一个会抛异常的 mock retriever
    mock_retriever = Mock(spec=Retriever)
    mock_retriever.search.side_effect = Exception("数据库连接失败")
    
    service = RAGService(retriever=mock_retriever)
    
    response = service.search_knowledge(
        keywords=["测试"],
        top_k=5,
        timeout=3.0
    )
    
    # 验证异常后降级
    assert response.degraded is True
    assert response.total_count == 0
    assert len(response.results) == 0
    assert "失败" in (response.message or "")


def test_batch_search_multiple_groups(rag_service: RAGService) -> None:
    """测试批量检索多个关键词组"""
    keyword_groups = [
        ["大安", "吉祥"],
        ["速喜", "喜事"],
        ["小吉", "平安"]
    ]
    
    results = rag_service.batch_search(
        keyword_groups=keyword_groups,
        top_k=3,
        timeout=3.0
    )
    
    assert len(results) == 3
    
    for key, response in results.items():
        assert isinstance(response.results, list)
        assert response.total_count >= 0


def test_batch_search_empty_groups(rag_service: RAGService) -> None:
    """测试批量检索空列表"""
    results = rag_service.batch_search(
        keyword_groups=[],
        top_k=5,
        timeout=3.0
    )
    
    assert len(results) == 0


def test_search_results_sorted_by_score(rag_service: RAGService) -> None:
    """测试结果按分数降序排列"""
    response = rag_service.search_knowledge(
        keywords=["小六壬", "占卜"],
        top_k=10,
        timeout=3.0
    )
    
    if len(response.results) > 1:
        for i in range(len(response.results) - 1):
            assert response.results[i].score >= response.results[i + 1].score
