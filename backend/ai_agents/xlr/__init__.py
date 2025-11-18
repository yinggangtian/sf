"""
XLR 小六壬算法包
"""

from .schemas import (
    QiguaRequest,
    QiguaInfo,
    PaipanResult,
    JieguaRequest,
    InterpretationResult,
    FindObjectRequest,
    FindObjectResult,
    ApiResponse,
    HistoryResponse,
    GongSchema,
    ShouSchema,
    QinSchema,
    DiZhiSchema
)

from .adapters.base import AlgorithmAdapter
from .adapters.liuren_adapter import LiurenAdapter

from .liuren.engine import PaipanEngine
from .liuren.jiegua_engine import JieguaEngine
from .liuren.utils import KnowledgeBase

__all__ = [
    # Schemas
    "QiguaRequest",
    "QiguaInfo",
    "PaipanResult",
    "JieguaRequest",
    "InterpretationResult",
    "FindObjectRequest",
    "FindObjectResult",
    "ApiResponse",
    "HistoryResponse",
    "GongSchema",
    "ShouSchema",
    "QinSchema",
    "DiZhiSchema",
    
    # Adapters
    "AlgorithmAdapter",
    "LiurenAdapter",
    
    # Engines
    "PaipanEngine",
    "JieguaEngine",
    "KnowledgeBase",
]
