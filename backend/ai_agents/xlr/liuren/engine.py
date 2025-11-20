"""
小六壬排盘引擎
负责起卦和排盘的核心计算
实现AR-01(起卦)和AR-02(排盘)的核心算法
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from ..schemas import QiguaInfo, PaipanResult
from .utils import KnowledgeBase


class PaipanEngine:
    """排盘引擎类"""
    
    # 地支阴阳分类
    YIN_DIZHI = ["丑", "卯", "巳", "未", "酉", "亥"]
    YANG_DIZHI = ["子", "寅", "辰", "午", "申", "戌"]
    
    # 六兽顺序
    LIUSHOU_ORDER = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]
    
    # 六兽起神规则 (根据地支定起始六兽)
    LIUSHOU_START_MAP = {
        "寅": "青龙", "卯": "青龙",
        "巳": "朱雀", "午": "朱雀",
        "丑": "勾陈", "辰": "勾陈",
        "未": "腾蛇", "戌": "腾蛇",
        "申": "白虎", "酉": "白虎",
        "亥": "玄武", "子": "玄武"
    }

    # 地支阴阳分类
    YIN_DIZHI = ["丑", "卯", "巳", "未", "酉", "亥"]
    YANG_DIZHI = ["子", "寅", "辰", "午", "申", "戌"]
    
    # 六兽顺序
    LIUSHOU_ORDER = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]
    
    # 六兽起神规则 (根据地支定起始六兽)
    LIUSHOU_START_MAP = {
        "寅": "青龙", "卯": "青龙",
        "巳": "朱雀", "午": "朱雀",
        "丑": "勾陈", "辰": "勾陈",
        "未": "腾蛇", "戌": "腾蛇",
        "申": "白虎", "酉": "白虎",
        "亥": "玄武", "子": "玄武"
    }

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
        
        # 计算体用关系
        ti_gong = qigua_info.number1  # 体宫 = 第一个数
        yong_gong = qigua_info.number2  # 用宫 = 第二个数
        
        # 更新 qigua_info 中的体用信息
        qigua_info.ti_gong = ti_gong
        qigua_info.yong_gong = yong_gong
        
        # 生成六宫排盘数据
        paipan_data = self._generate_liugong_paipan(luogong, qigua_info.shichen_info, ti_gong, yong_gong)
        
        # 添加六兽排盘
        paipan_data = self._add_liushou_paipan(paipan_data, luogong)
        
        # 添加六亲排盘
        paipan_data = self._add_liuqin_paipan(paipan_data, luogong)
        
        # 添加五行关系分析
        paipan_data = self._add_wuxing_analysis(paipan_data)
        
        return PaipanResult(
            qigua_info=qigua_info,
            paipan_data=paipan_data,
            creation_time=datetime.now()
        )
        
    def _generate_liugong_paipan(self, luogong: int, shichen_info: Dict[str, Any], ti_gong: Optional[int] = None, yong_gong: Optional[int] = None) -> Dict[str, Any]:
        """
        生成六宫排盘数据 (Step 2)
        """
        gong_paipan = {}
        
        # 1. 获取当前时辰地支 (太极点地支)
        current_dizhi_name = shichen_info["dizhi"]
        
        # 2. 获取地支序列 (阴阳顺排)
        dizhi_seq = self._get_dizhi_sequence(current_dizhi_name)
        
        # 3. 旋转序列，使得 current_dizhi 位于 luogong 位置 (index = luogong - 1)
        rotated_dizhis = self._rotate_list(dizhi_seq, current_dizhi_name, luogong - 1)
        
        # 六宫固定顺序：大安、留连、速喜、赤口、小吉、空亡
        gong_positions = [1, 2, 3, 4, 5, 6]
        
        for i, pos in enumerate(gong_positions):
            gong = self.knowledge_base.get_gong_by_position(pos)
            
            # 获取该位置对应的地支
            dizhi_name = rotated_dizhis[i]
            dizhi_obj = self.knowledge_base.get_dizhi_by_name(dizhi_name)
            
            if gong:
                gong_paipan[f"gong_{pos}"] = {
                    "name": gong.name,
                    "position": pos,
                    "wuxing": gong.wuxing,
                    "meaning": gong.meaning,
                    "is_luogong": pos == luogong,
                    "is_ti_gong": pos == ti_gong,
                    "is_yong_gong": pos == yong_gong,
                    "attributes": gong.attributes or {},
                    # 添加地支信息
                    "dizhi_info": {
                        "name": dizhi_obj.name,
                        "wuxing": dizhi_obj.wuxing,
                        "shichen": dizhi_obj.shichen,
                        "meaning": dizhi_obj.meaning
                    } if dizhi_obj else {}
                }
                
        # 添加时辰信息到排盘
        gong_paipan["shichen_info"] = shichen_info
        gong_paipan["luogong_position"] = luogong
        gong_paipan["ti_gong_position"] = ti_gong
        gong_paipan["yong_gong_position"] = yong_gong
        
        # 获取体用宫的详细信息
        if ti_gong:
            ti_gong_obj = self.knowledge_base.get_gong_by_position(ti_gong)
            gong_paipan["ti_gong_info"] = {
                "name": ti_gong_obj.name,
                "position": ti_gong,
                "wuxing": ti_gong_obj.wuxing,
                "meaning": ti_gong_obj.meaning
            } if ti_gong_obj else None
        
        if yong_gong:
            yong_gong_obj = self.knowledge_base.get_gong_by_position(yong_gong)
            gong_paipan["yong_gong_info"] = {
                "name": yong_gong_obj.name,
                "position": yong_gong,
                "wuxing": yong_gong_obj.wuxing,
                "meaning": yong_gong_obj.meaning
            } if yong_gong_obj else None
        
        return {"liugong": gong_paipan}
        
    def _add_liushou_paipan(self, paipan_data: Dict[str, Any], luogong: int) -> Dict[str, Any]:
        """
        添加六兽排盘数据 (Step 3)
        """
        liushou_paipan = {}
        
        # 1. 获取太极点地支 (luogong 位置的地支)
        # 注意：Step 3 规则是 "寅卯起青龙" 等，通常是指根据"日支"或"时支"起，
        # 但 XLR.md 示例中，似乎是根据"宫位地支"来排？
        # 让我们再看一遍 XLR.md 的 Step 3.
        # "根据地支神兽对应关系落六兽"
        # 示例：
        # 1 | 酉 | 白虎
        # 2 | 亥 | 玄武
        # ...
        # 这里的逻辑是：
        # 宫位1的地支是酉 -> 申酉起白虎 -> 宫位1是白虎
        # 然后按顺序排？
        # 如果宫位1是白虎，那么宫位2是玄武，宫位3是青龙...
        # 这与示例完全一致。
        # 所以逻辑是：
        # 1. 看宫位1 (大安) 的地支。
        # 2. 根据该地支确定起始六兽。
        # 3. 从宫位1开始顺排六兽。
        
        gong_1_key = "gong_1"
        if gong_1_key not in paipan_data["liugong"]:
            return paipan_data
            
        gong_1_dizhi_info = paipan_data["liugong"][gong_1_key].get("dizhi_info")
        if not gong_1_dizhi_info:
            return paipan_data
            
        gong_1_dizhi_name = gong_1_dizhi_info["name"]
        
        # 2. 根据地支确定起始六兽
        start_shou_name = self.LIUSHOU_START_MAP.get(gong_1_dizhi_name)
        if not start_shou_name:
            # 如果找不到映射（理论上不应该），默认青龙？或者报错？
            # 这里做个容错，默认青龙
            start_shou_name = "青龙"
            
        # 3. 旋转六兽序列，使得 start_shou 位于 index 0 (即宫位1)
        # LIUSHOU_ORDER = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]
        # 如果 start 是 白虎 (index 4)，我们要让白虎排在第一个。
        # rotate_list(list, target, target_pos) -> target at target_pos
        # 我们要 start_shou at pos 0 (index 0)
        rotated_shous = self._rotate_list(self.LIUSHOU_ORDER, start_shou_name, 0)
        
        for i in range(6):
            pos = i + 1
            shou_name = rotated_shous[i]
            
            # 查找六兽对象
            shou_obj = None
            for s in self.knowledge_base.get_all_shou():
                if s.name == shou_name:
                    shou_obj = s
                    break
            
            if shou_obj:
                liushou_paipan[f"shou_{pos}"] = {
                    "name": shou_obj.name,
                    "gong_position": pos,
                    "wuxing": shou_obj.wuxing,
                    "characteristics": shou_obj.characteristics,
                    "meaning": shou_obj.meaning,
                    "attributes": shou_obj.attributes or {}
                }
                
        paipan_data["liushou"] = liushou_paipan
        return paipan_data

    def _add_liuqin_paipan(self, paipan_data: Dict[str, Any], luogong: int) -> Dict[str, Any]:
        """
        添加六亲排盘数据 (Step 4)
        """
        liuqin_paipan = {}
        
        # 1. 获取太极点地支五行 (作为"我")
        luogong_key = f"gong_{luogong}"
        if luogong_key not in paipan_data["liugong"]:
            return paipan_data
            
        taiji_dizhi_info = paipan_data["liugong"][luogong_key].get("dizhi_info")
        if not taiji_dizhi_info:
            return paipan_data
            
        taiji_wuxing = taiji_dizhi_info["wuxing"]
        
        # 2. 遍历各宫，计算六亲
        for i in range(1, 7):
            gong_key = f"gong_{i}"
            gong_data = paipan_data["liugong"].get(gong_key)
            if not gong_data:
                continue
                
            current_dizhi_info = gong_data.get("dizhi_info")
            if not current_dizhi_info:
                continue
                
            current_wuxing = current_dizhi_info["wuxing"]
            
            # 计算关系
            relation_name = self._calculate_liuqin_relation(taiji_wuxing, current_wuxing, is_self=(i == luogong))
            
            # 获取六亲详细信息
            qin_obj = None
            for q in self.knowledge_base.get_all_qin():
                if q.name == relation_name:
                    qin_obj = q
                    break
            
            liuqin_paipan[f"qin_{i}"] = {
                "name": relation_name,
                "gong_position": i,
                "dizhi_wuxing": current_wuxing,
                "taiji_wuxing": taiji_wuxing,
                "meaning": qin_obj.meaning if qin_obj else "",
                "relationship": qin_obj.relationship if qin_obj else "",
                "attributes": qin_obj.attributes if qin_obj else {}
            }
            
        paipan_data["liuqin"] = liuqin_paipan
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

    def _get_dizhi_sequence(self, current_dizhi: str) -> List[str]:
        """
        根据当前地支获取地支排列顺序 (阴阳顺排)
        """
        if current_dizhi in self.YIN_DIZHI:
            return self.YIN_DIZHI
        return self.YANG_DIZHI

    def _rotate_list(self, lst: List[Any], target_item: Any, target_pos_index: int) -> List[Any]:
        """
        旋转列表，使得 target_item 出现在 target_pos_index 位置 (0-based index)
        """
        if target_item not in lst:
            return lst
            
        n = len(lst)
        current_idx = lst.index(target_item)
        
        # 计算起始元素的索引
        # 如果 target_item 在 target_pos_index
        # 那么 index 0 的元素应该是 target_item 往前推 target_pos_index 个位置的元素
        # 例如：[A, B, C], target=B (idx=1), target_pos=0
        # start_idx = (1 - 0) = 1 -> B starts. [B, C, A]
        # 例如：[A, B, C], target=B (idx=1), target_pos=1
        # start_idx = (1 - 1) = 0 -> A starts. [A, B, C]
        start_item_idx = (current_idx - target_pos_index) % n
        
        result = []
        for i in range(n):
            result.append(lst[(start_item_idx + i) % n])
            
        return result

    def _calculate_liuqin_relation(self, me_wuxing: str, other_wuxing: str, is_self: bool) -> str:
        """
        计算六亲关系
        """
        # Step 4 示例中，Pos 2 (Hai) 是太极点，六亲是 "我"。
        # Pos 2 (Hai) is Water. Me is Water.
        # 统一用 "兄弟" (同五行) 或 "自身" (太极点)
        # 这里我们返回 "兄弟" 作为同五行的标准六亲名称，
        # 但如果是太极点本身，也许应该特殊标记？
        # XLR.md 示例表格中写的是 "我 (同五行)"，但 Prompt 定义里有 "自身"。
        # Prompt: <六亲>自身、父母、兄弟、子孙、官鬼、妻财</六亲>
        # 我们可以返回 "兄弟"，然后在 Prompt 阶段处理 "自身"？
        # 或者如果 is_self 为 True，直接返回 "自身"？
        # 让我们看看 Prompt 里的定义。
        # Prompt 2: <六亲>自身、父母、兄弟、子孙、官鬼、妻财</六亲>
        # 所以 "自身" 是一个有效的六亲类别。
        
        if is_self:
             return "自身"

        relation = self.knowledge_base.get_wuxing_relation(me_wuxing, other_wuxing)
        
        # relation string from DB might be "生", "克", "生我", "克我", "同"
        # Map to Liuqin
        if relation == "生": # Me generate Other
            return "子孙"
        elif relation == "克": # Me overcome Other
            return "妻财"
        elif relation == "生我": # Other generate Me
            return "父母"
        elif relation == "克我": # Other overcome Me
            return "官鬼"
        elif relation == "同": # Same
            return "兄弟"
        else:
            return "未知"
