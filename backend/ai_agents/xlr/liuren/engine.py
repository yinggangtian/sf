"""
小六壬排盘引擎
负责起卦和排盘的核心计算
实现AR-01(起卦)和AR-02(排盘)的核心算法
"""

from datetime import datetime
from typing import Dict, Any
from ..schemas import QiguaInfo, PaipanResult
from .utils import KnowledgeBase


class PaipanEngine:
    """排盘引擎类"""
    
    def __init__(self, kb: KnowledgeBase):
        """
        初始化排盘引擎
        
        Args:
            kb: 知识库实例
        """
        self.knowledge_base = kb
        
    def calculate_luogong(self, num1: int, num2: int) -> int:
        """
        计算落宫位置 (AR-01-03 算法)
        
        Args:
            num1: 第一个报数(1-6)
            num2: 第二个报数(1-6) 
            
        Returns:
            落宫位置(1-6)
        """
        # 小六壬落宫算法：(第一个数 + 第二个数 - 1) % 6 + 1
        # 如果结果为0，则为6
        result = (num1 + num2 - 1) % 6
        return result if result != 0 else 6
        
    def get_shichen_info(self, dt: datetime) -> Dict[str, Any]:
        """
        获取时辰信息 (AR-01-02 算法)
        
        Args:
            dt: 起卦时间
            
        Returns:
            时辰相关信息字典
        """
        # 地支时辰对照表 (时辰, 起始小时, 结束小时)
        dizhi_hours = [
            ("子", 23, 1), ("丑", 1, 3), ("寅", 3, 5), ("卯", 5, 7),
            ("辰", 7, 9), ("巳", 9, 11), ("午", 11, 13), ("未", 13, 15),
            ("申", 15, 17), ("酉", 17, 19), ("戌", 19, 21), ("亥", 21, 23)
        ]
        
        hour = dt.hour
        current_dizhi = None
        
        # 确定当前时辰
        for dizhi, start_hour, end_hour in dizhi_hours:
            if start_hour <= hour < end_hour or (start_hour == 23 and hour >= 23):
                current_dizhi = dizhi
                break
        
        if current_dizhi is None:  # 处理子时的特殊情况 (0点到1点)
            current_dizhi = "子"
            
        # 获取地支详细信息
        dizhi_info = self.knowledge_base.get_dizhi_by_name(current_dizhi)
        
        return {
            "dizhi": current_dizhi,
            "hour": hour,
            "dizhi_info": {
                "name": dizhi_info.name,
                "wuxing": dizhi_info.wuxing,
                "shichen": dizhi_info.shichen,
                "meaning": dizhi_info.meaning,
            } if dizhi_info else {},
            "year": dt.year,
            "month": dt.month,
            "day": dt.day
        }
        
    def generate_paipan(self, qigua_info: QiguaInfo) -> PaipanResult:
        """
        生成完整排盘 (AR-02-01, AR-02-03 逻辑)
        
        Args:
            qigua_info: 起卦信息
            
        Returns:
            完整的排盘结果
        """
        luogong = qigua_info.luogong
        
        # 生成六宫排盘数据
        paipan_data = self._generate_liugong_paipan(luogong, qigua_info.shichen_info)
        
        # 添加六兽排盘
        paipan_data = self._add_liushou_paipan(paipan_data, luogong)
        
        # 添加五行关系分析
        paipan_data = self._add_wuxing_analysis(paipan_data)
        
        return PaipanResult(
            qigua_info=qigua_info,
            paipan_data=paipan_data,
            creation_time=datetime.now()
        )
        
    def _generate_liugong_paipan(self, luogong: int, shichen_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成六宫排盘数据
        
        Args:
            luogong: 落宫位置
            shichen_info: 时辰信息
            
        Returns:
            六宫排盘数据字典
        """
        gong_paipan = {}
        
        # 六宫固定顺序：大安、留连、速喜、赤口、小吉、空亡
        gong_positions = [1, 2, 3, 4, 5, 6]  # 对应大安到空亡
        
        for i, pos in enumerate(gong_positions):
            gong = self.knowledge_base.get_gong_by_position(pos)
            if gong:
                gong_paipan[f"gong_{pos}"] = {
                    "name": gong.name,
                    "position": pos,
                    "wuxing": gong.wuxing,
                    "meaning": gong.meaning,
                    "is_luogong": pos == luogong,
                    "attributes": gong.attributes or {}
                }
                
        # 添加时辰信息到排盘
        gong_paipan["shichen_info"] = shichen_info
        gong_paipan["luogong_position"] = luogong
        
        return {"liugong": gong_paipan}
        
    def _add_liushou_paipan(self, paipan_data: Dict[str, Any], luogong: int) -> Dict[str, Any]:
        """
        添加六兽排盘数据
        
        Args:
            paipan_data: 现有排盘数据
            luogong: 落宫位置
            
        Returns:
            添加六兽后的排盘数据
        """
        liushou_paipan = {}
        
        # 六兽从落宫开始排列
        shou_positions = [(luogong + i - 1) % 6 + 1 for i in range(6)]
        
        for i, pos in enumerate(shou_positions):
            shou = self.knowledge_base.get_shou_by_position((i + 1))
            gong_pos = pos
            
            if shou:
                liushou_paipan[f"shou_{i+1}"] = {
                    "name": shou.name,
                    "gong_position": gong_pos,
                    "wuxing": shou.wuxing,
                    "characteristics": shou.characteristics,
                    "meaning": shou.meaning,
                    "attributes": shou.attributes or {}
                }
                
        paipan_data["liushou"] = liushou_paipan
        return paipan_data
        
    def _add_wuxing_analysis(self, paipan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加五行关系分析
        
        Args:
            paipan_data: 现有排盘数据
            
        Returns:
            添加五行分析后的排盘数据
        """
        wuxing_analysis = {
            "elements_present": [],
            "element_relations": {},
            "balance_analysis": {}
        }
        
        # 收集所有五行元素
        elements = set()
        if "liugong" in paipan_data:
            for gong_key, gong_info in paipan_data["liugong"].items():
                if isinstance(gong_info, dict) and "wuxing" in gong_info:
                    elements.add(gong_info["wuxing"])
                    
        if "liushou" in paipan_data:
            for shou_key, shou_info in paipan_data["liushou"].items():
                if isinstance(shou_info, dict) and "wuxing" in shou_info:
                    elements.add(shou_info["wuxing"])
        
        wuxing_analysis["elements_present"] = list(elements)
        
        # 分析五行关系
        for elem1 in elements:
            relations = {}
            for elem2 in elements:
                if elem1 != elem2:
                    relation = self.knowledge_base.get_wuxing_relation(elem1, elem2)
                    relations[elem2] = relation
            wuxing_analysis["element_relations"][elem1] = relations
            
        paipan_data["wuxing_analysis"] = wuxing_analysis
        return paipan_data
