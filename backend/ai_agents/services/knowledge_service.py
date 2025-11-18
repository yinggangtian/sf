"""
知识库服务层
负责知识库数据的加载、缓存和管理
"""

from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from ..xlr.liuren.utils import KnowledgeBase
from backend.shared.db.models.knowledge import Gong, Shou, Qin, DiZhi, WuxingRelation


class KnowledgeService:
    """知识库服务类"""
    
    def __init__(self, db_session: Session, cache_service: Optional[Any] = None):
        """
        初始化知识库服务
        
        Args:
            db_session: 数据库会话
            cache_service: 缓存服务(可选)
        """
        self.db_session = db_session
        self.cache_service = cache_service
        self._cached_kb: Optional[KnowledgeBase] = None
        
    def get_knowledge_base(self, force_reload: bool = False) -> KnowledgeBase:
        """
        获取知识库（优先从缓存获取）
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            知识库对象
        """
        # 如果强制重新加载或内存中没有缓存，则重新获取
        if force_reload or self._cached_kb is None:
            # 首先尝试从缓存获取(如果有缓存服务)
            if self.cache_service:
                cached_kb = self.cache_service.get("knowledge_base")
                if cached_kb and isinstance(cached_kb, KnowledgeBase) and cached_kb.is_loaded():
                    self._cached_kb = cached_kb
                    return self._cached_kb
                
            # 缓存未命中，从数据库加载
            self._cached_kb = self._load_from_database()
            
            # 加载成功后存入缓存
            if self.cache_service and self._cached_kb and self._cached_kb.is_loaded():
                self.cache_service.set("knowledge_base", self._cached_kb, ttl=3600)
                
        return self._cached_kb
        
    def refresh_knowledge_base(self) -> KnowledgeBase:
        """
        刷新知识库（强制从数据库重新加载）
        
        Returns:
            知识库对象
        """
        return self.get_knowledge_base(force_reload=True)
        
    def get_gong_by_position(self, position: int) -> Optional[Gong]:
        """
        根据位置获取宫位信息
        
        Args:
            position: 宫位位置(1-6)
            
        Returns:
            宫位对象或None
        """
        return self.db_session.query(Gong).filter(Gong.position == position).first()
        
    def get_shou_by_position(self, position: int) -> Optional[Shou]:
        """
        根据位置获取六兽信息
        
        Args:
            position: 六兽位置(1-6)
            
        Returns:
            六兽对象或None
        """
        return self.db_session.query(Shou).filter(Shou.position == position).first()
        
    def get_dizhi_by_name(self, name: str) -> Optional[DiZhi]:
        """
        根据名称获取地支信息
        
        Args:
            name: 地支名称
            
        Returns:
            地支对象或None
        """
        return self.db_session.query(DiZhi).filter(DiZhi.name == name).first()
        
    def get_all_gong(self) -> List[Gong]:
        """获取所有宫位数据"""
        return self.db_session.query(Gong).order_by(Gong.position).all()
        
    def get_all_shou(self) -> List[Shou]:
        """获取所有六兽数据"""
        return self.db_session.query(Shou).order_by(Shou.position).all()
        
    def get_all_qin(self) -> List[Qin]:
        """获取所有六亲数据"""
        return self.db_session.query(Qin).all()
        
    def get_all_dizhi(self) -> List[DiZhi]:
        """获取所有地支数据"""
        return self.db_session.query(DiZhi).order_by(DiZhi.order).all()
        
    # ==================== 内部辅助方法 ====================
    
    def _load_from_database(self) -> KnowledgeBase:
        """
        从数据库加载知识库
        
        Returns:
            知识库对象
        """
        kb = KnowledgeBase()
        
        try:
            # 加载六宫数据
            gong_data = self.get_all_gong()
            kb.load_gong_data(gong_data)
            
            # 加载六兽数据
            shou_data = self.get_all_shou()
            kb.load_shou_data(shou_data)
            
            # 加载六亲数据
            qin_data = self.get_all_qin()
            kb.load_qin_data(qin_data)
            
            # 加载地支数据
            dizhi_data = self.get_all_dizhi()
            kb.load_dizhi_data(dizhi_data)
            
            # 加载五行关系数据
            wuxing_relations = self._load_wuxing_relations()
            kb.load_wuxing_relations(wuxing_relations)
            
            print(f"✅ 知识库加载完成: 六宫{len(gong_data)}个, 六兽{len(shou_data)}个, "
                  f"六亲{len(qin_data)}个, 地支{len(dizhi_data)}个")
                  
        except Exception as e:
            print(f"❌ 知识库加载失败: {e}")
            raise RuntimeError(f"知识库加载失败: {e}") from e
            
        return kb
        
    def _load_wuxing_relations(self) -> Dict[str, Dict[str, str]]:
        """
        从数据库加载五行关系
        
        Returns:
            五行关系字典
        """
        relations: Dict[str, Dict[str, str]] = {}
        
        # 查询所有五行关系记录
        wuxing_records = self.db_session.query(WuxingRelation).all()
        
        for record in wuxing_records:
            if record.element1 not in relations:
                relations[record.element1] = {}
            relations[record.element1][record.element2] = record.relation
            
        # 如果数据库中没有五行关系数据，使用默认关系
        if not relations:
            relations = self._get_default_wuxing_relations()
            
        return relations
        
    def _get_default_wuxing_relations(self) -> Dict[str, Dict[str, str]]:
        """
        获取默认五行关系
        
        Returns:
            默认五行关系字典
        """
        return {
            "金": {"木": "克", "水": "生", "火": "克我", "土": "生我", "金": "同"},
            "木": {"火": "生", "土": "克", "金": "克我", "水": "生我", "木": "同"},
            "水": {"木": "生", "火": "克", "土": "克我", "金": "生我", "水": "同"},
            "火": {"土": "生", "金": "克", "水": "克我", "木": "生我", "火": "同"},
            "土": {"金": "生", "水": "克", "木": "克我", "火": "生我", "土": "同"}
        }


# 为了避免 circular import，定义 Any 类型
from typing import Any
