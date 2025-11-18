"""
小六壬知识库工具类
提供知识库数据的加载和查询功能
"""

from typing import List, Dict, Any, Optional
from backend.shared.db.models.knowledge import Gong, Shou, Qin, DiZhi


class KnowledgeBase:
    """知识库数据容器类"""
    
    def __init__(self):
        self.gong_data: List[Gong] = []
        self.shou_data: List[Shou] = []
        self.qin_data: List[Qin] = []
        self.dizhi_data: List[DiZhi] = []
        self.wuxing_relations: Dict[str, Dict[str, str]] = {}
        self.gong_mapping: Dict[int, Gong] = {}
        self.shou_mapping: Dict[int, Shou] = {}
        self.dizhi_mapping: Dict[str, DiZhi] = {}
        
    def load_gong_data(self, gong_list: List[Gong]) -> None:
        """加载六宫数据"""
        self.gong_data = gong_list
        self.gong_mapping = {gong.position: gong for gong in gong_list}
        
    def load_shou_data(self, shou_list: List[Shou]) -> None:
        """加载六兽数据"""
        self.shou_data = shou_list
        self.shou_mapping = {shou.position: shou for shou in shou_list}
        
    def load_qin_data(self, qin_list: List[Qin]) -> None:
        """加载六亲数据"""
        self.qin_data = qin_list
        
    def load_dizhi_data(self, dizhi_list: List[DiZhi]) -> None:
        """加载地支数据"""
        self.dizhi_data = dizhi_list
        self.dizhi_mapping = {dizhi.name: dizhi for dizhi in dizhi_list}
        
    def load_wuxing_relations(self, relations: Dict[str, Dict[str, str]]) -> None:
        """
        加载五行关系数据
        格式: {"金": {"木": "克", "水": "生", ...}, ...}
        """
        self.wuxing_relations = relations
        
    def get_gong_by_position(self, position: int) -> Optional[Gong]:
        """根据位置获取宫位信息"""
        return self.gong_mapping.get(position)
        
    def get_shou_by_position(self, position: int) -> Optional[Shou]:
        """根据位置获取六兽信息"""
        return self.shou_mapping.get(position)
        
    def get_dizhi_by_name(self, name: str) -> Optional[DiZhi]:
        """根据名称获取地支信息"""
        return self.dizhi_mapping.get(name)
        
    def get_wuxing_relation(self, element1: str, element2: str) -> str:
        """获取两个五行之间的关系"""
        if element1 not in self.wuxing_relations:
            return "无关"
        relations = self.wuxing_relations[element1]
        return relations.get(element2, "无关")
        
    def is_loaded(self) -> bool:
        """检查知识库是否已加载完成"""
        return (
            len(self.gong_data) > 0 and
            len(self.shou_data) > 0 and
            len(self.qin_data) > 0 and
            len(self.dizhi_data) > 0
        )
        
    def get_all_gong(self) -> List[Gong]:
        """获取所有六宫数据"""
        return self.gong_data
        
    def get_all_shou(self) -> List[Shou]:
        """获取所有六兽数据"""
        return self.shou_data
        
    def get_all_qin(self) -> List[Qin]:
        """获取所有六亲数据"""
        return self.qin_data
        
    def get_all_dizhi(self) -> List[DiZhi]:
        """获取所有地支数据"""
        return self.dizhi_data
