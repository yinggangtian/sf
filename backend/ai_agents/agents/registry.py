"""算法适配器注册表与路由逻辑。"""

from __future__ import annotations

from typing import Dict, Optional

from backend.ai_agents.xlr.adapters.liuren_adapter import LiurenAdapter
from backend.ai_agents.xlr.liuren.utils import KnowledgeBase

from backend.ai_agents.xlr.adapters.base import AlgorithmAdapter


class AlgorithmRegistry:
    """维护算法适配器实例的注册表。"""

    def __init__(self) -> None:
        self._adapters: Dict[str, AlgorithmAdapter] = {}

    def register(self, adapter: AlgorithmAdapter) -> None:
        """注册一个算法适配器。"""
        name = adapter.get_name()
        if name in self._adapters:
            raise ValueError(f"算法适配器 '{name}' 已注册")
        self._adapters[name] = adapter

    def get(self, adapter_id: str) -> Optional[AlgorithmAdapter]:
        """根据适配器ID获取实例。"""
        return self._adapters.get(adapter_id)

    def route(self, algorithm_hint: Optional[str]) -> Optional[AlgorithmAdapter]:
        """根据路由提示选择相应适配器。"""
        if algorithm_hint and algorithm_hint in self._adapters:
            return self._adapters[algorithm_hint]
        return None

    def clear(self) -> None:
        """清空注册表（用于测试）。"""
        self._adapters.clear()


registry = AlgorithmRegistry()
"""默认的全局算法注册表。"""


def bootstrap_default_adapters(kb: KnowledgeBase) -> None:
    """向全局注册表注入默认算法适配器。"""
    if registry.get("xlr-liuren") is None:
        registry.register(LiurenAdapter(kb))
