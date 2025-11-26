"""FastAPI dependencies
提供依赖注入：数据库会话、当前用户、Agent 实例等
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.shared.db.session import SessionLocal
from backend.shared.db.models.user import User
from backend.shared.db.models.knowledge import Gong, Shou, Qin, DiZhi
from backend.ai_agents.agents.master_agent import MasterAgent
from backend.ai_agents.agents.orchestrator import OrchestratorAgent
from backend.ai_agents.agents.explainer import ExplainerAgent
from backend.ai_agents.agents.registry import AlgorithmRegistry
from backend.ai_agents.services.divination_service import DivinationService
from backend.ai_agents.services.rag_service import RAGService
from backend.ai_agents.services.memory_service import MemoryService
from backend.ai_agents.xlr.adapters.liuren_adapter import LiurenAdapter
from backend.ai_agents.xlr.liuren.utils import KnowledgeBase


# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（依赖注入）
    
    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    获取当前用户（从 JWT Token）
    
    Args:
        credentials: HTTP Bearer 凭证
        db: 数据库会话
        
    Returns:
        当前用户或 None（暂时返回 None，待实现 JWT 验证）
        
    Raises:
        HTTPException: 401 未授权
    """
    # TODO: 实现 JWT Token 验证
    # 当前 MVP 阶段暂不强制认证，返回 None
    # 后续需要：
    # 1. 解析 JWT Token
    # 2. 验证签名和过期时间
    # 3. 从数据库查询用户
    # 4. 返回用户对象
    
    if credentials is None:
        # 暂时允许无认证访问（MVP）
        return None
    
    # 这里应该验证 token 并返回用户
    # token = credentials.credentials
    # user_id = verify_jwt_token(token)
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=401, detail="用户不存在")
    # return user
    return None


def get_master_agent(db: Session = Depends(get_db)) -> MasterAgent:
    """
    获取 MasterAgent 实例（依赖注入）
    
    Args:
        db: 数据库会话
        
    Returns:
        MasterAgent 实例
    """
    # 加载知识库数据
    kb = KnowledgeBase()
    
    # 从数据库加载六宫、六兽、六亲、地支数据
    gong_list = db.query(Gong).order_by(Gong.position).all()
    shou_list = db.query(Shou).order_by(Shou.position).all()
    qin_list = db.query(Qin).all()
    dizhi_list = db.query(DiZhi).all()
    
    kb.load_gong_data(gong_list)
    kb.load_shou_data(shou_list)
    kb.load_qin_data(qin_list)
    kb.load_dizhi_data(dizhi_list)
    
    # 初始化算法适配器
    liuren_adapter = LiurenAdapter(knowledge_base=kb)
    
    # 初始化算法注册表
    algorithm_registry = AlgorithmRegistry()
    algorithm_registry.register(liuren_adapter)
    
    # 初始化服务层
    divination_service = DivinationService(
        liuren_adapter=liuren_adapter,
        db_session=db
    )
    rag_service = RAGService(db_session=db)
    memory_service = MemoryService(db_session=db)
    
    # 初始化 Agent
    orchestrator = OrchestratorAgent()
    explainer = ExplainerAgent()
    
    # 组装 MasterAgent
    master_agent = MasterAgent(
        orchestrator=orchestrator,
        explainer=explainer,
        algorithm_registry=algorithm_registry,
        divination_service=divination_service,
        rag_service=rag_service,
        memory_service=memory_service,
        tool_timeout=30.0
    )
    
    return master_agent


def get_divination_service(db: Session = Depends(get_db)) -> DivinationService:
    """
    获取 DivinationService 实例（依赖注入）
    
    Args:
        db: 数据库会话
        
    Returns:
        DivinationService 实例
    """
    # 加载知识库数据
    kb = KnowledgeBase()
    
    gong_list = db.query(Gong).order_by(Gong.position).all()
    shou_list = db.query(Shou).order_by(Shou.position).all()
    qin_list = db.query(Qin).all()
    dizhi_list = db.query(DiZhi).all()
    
    kb.load_gong_data(gong_list)
    kb.load_shou_data(shou_list)
    kb.load_qin_data(qin_list)
    kb.load_dizhi_data(dizhi_list)
    
    liuren_adapter = LiurenAdapter(knowledge_base=kb)
    return DivinationService(
        liuren_adapter=liuren_adapter,
        db_session=db
    )
