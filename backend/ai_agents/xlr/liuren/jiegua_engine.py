"""
解卦引擎辅助类
提供解卦相关的核心算法和分析功能
"""

from typing import List, Dict, Any
from ..schemas import PaipanResult, InterpretationResult, FindObjectResult
from ..liuren.utils import KnowledgeBase


class JieguaEngine:
    """解卦引擎类"""
    
    def __init__(self, kb: KnowledgeBase):
        """
        初始化解卦引擎
        
        Args:
            kb: 知识库实例
        """
        self.knowledge_base = kb
        
    def select_yongshen(self, question_type: str, gender: str) -> List[str]:
        """
        选择用神 (AR-03-02 逻辑)
        
        Args:
            question_type: 问题类型
            gender: 性别
            
        Returns:
            用神列表
        """
        yongshen_mapping = {
            "事业": ["官鬼", "父母"],
            "财运": ["妻财", "官鬼"],
            "感情": ["世爻", "应爻", "妻财"] if gender == "男" else ["世爻", "应爻", "官鬼"],
            "健康": ["世爻", "父母"],
            "学业": ["父母", "官鬼"],
            "出行": ["父母", "子孙"],
            "官司": ["官鬼", "父母"],
            "寻物": ["妻财", "父母"],
            "通用": ["世爻", "用神"]
        }
        
        return yongshen_mapping.get(question_type, yongshen_mapping["通用"])
        
    def analyze_gong(self, paipan: PaipanResult, yongshen: str) -> Dict[str, Any]:
        """
        分析宫位 (AR-03-03 逻辑)
        
        Args:
            paipan: 排盘结果
            yongshen: 用神
            
        Returns:
            宫位分析结果
        """
        analysis = {
            "luogong_analysis": {},
            "related_gong_analysis": {},
            "yongshen_position": {},
            "strength_analysis": {}
        }
        
        luogong_pos = paipan.paipan_data.get("liugong", {}).get("luogong_position", 1)
        
        # 分析落宫
        luogong_info = paipan.paipan_data.get("liugong", {}).get(f"gong_{luogong_pos}", {})
        if luogong_info:
            analysis["luogong_analysis"] = {
                "name": luogong_info.get("name", ""),
                "wuxing": luogong_info.get("wuxing", ""),
                "meaning": luogong_info.get("meaning", ""),
                "favorable": self._is_favorable_gong(luogong_info.get("name", "")),
                "interpretation": self._interpret_gong_meaning(luogong_info.get("name", ""), yongshen)
            }
            
        # 分析相关宫位
        related_positions = self._get_related_positions(luogong_pos)
        for pos in related_positions:
            gong_info = paipan.paipan_data.get("liugong", {}).get(f"gong_{pos}", {})
            if gong_info:
                analysis["related_gong_analysis"][f"gong_{pos}"] = {
                    "name": gong_info.get("name", ""),
                    "relation_to_luogong": self._analyze_gong_relation(luogong_pos, pos),
                    "influence": self._calculate_influence(gong_info, luogong_info)
                }
                
        return analysis
        
    def generate_interpretation(self, paipan: PaipanResult, question_type: str, gender: str) -> InterpretationResult:
        """
        生成综合解读 (AR-03-07 综合解读)
        
        Args:
            paipan: 排盘结果
            question_type: 问题类型
            gender: 性别
            
        Returns:
            解卦结果
        """
        # 选择用神
        yongshen_list = self.select_yongshen(question_type, gender)
        
        # 分析主要用神
        main_yongshen = yongshen_list[0] if yongshen_list else "世爻"
        gong_analysis = self.analyze_gong(paipan, main_yongshen)
        
        # 生成综合解读
        comprehensive_text = self._generate_comprehensive_text(
            paipan, question_type, gong_analysis, yongshen_list
        )
        
        # 详细分析
        detailed_analysis = self._generate_detailed_analysis(
            paipan, question_type, gong_analysis, yongshen_list
        )
        
        return InterpretationResult(
            yongshen=yongshen_list,
            gong_analysis=gong_analysis,
            comprehensive_interpretation=comprehensive_text,
            detailed_analysis=detailed_analysis
        )
        
    def analyze_find_object(self, paipan: PaipanResult, item_desc: str) -> FindObjectResult:
        """
        寻物专项分析 (AR-09 专项功能)
        
        Args:
            paipan: 排盘结果
            item_desc: 物品描述
            
        Returns:
            寻物分析结果
        """
        luogong_pos = paipan.paipan_data.get("liugong", {}).get("luogong_position", 1)
        luogong_info = paipan.paipan_data.get("liugong", {}).get(f"gong_{luogong_pos}", {})
        
        # 方位分析
        direction_analysis = self._analyze_direction(luogong_info, item_desc)
        
        # 位置线索
        location_clues = self._generate_location_clues(luogong_info, item_desc)
        
        # 时间估计
        time_estimation = self._estimate_find_time(luogong_info)
        
        # 成功概率
        success_probability = self._calculate_success_probability(luogong_info)
        
        # 详细指导
        detailed_guidance = self._generate_find_guidance(
            direction_analysis, location_clues, time_estimation, success_probability
        )
        
        return FindObjectResult(
            direction_analysis=direction_analysis,
            location_clues=location_clues,
            time_estimation=time_estimation,
            success_probability=success_probability,
            detailed_guidance=detailed_guidance
        )
        
    # ==================== 内部辅助方法 ====================
    
    def _is_favorable_gong(self, gong_name: str) -> bool:
        """判断宫位是否有利"""
        favorable_gongs = ["大安", "速喜", "小吉"]
        return gong_name in favorable_gongs
        
    def _interpret_gong_meaning(self, gong_name: str, yongshen: str) -> str:
        """解释宫位含义"""
        interpretations = {
            "大安": f"平安吉利，{yongshen}得位，事情顺利发展",
            "留连": f"事情拖延，{yongshen}受困，需要耐心等待",
            "速喜": f"快速喜悦，{yongshen}得力，事情进展迅速",
            "赤口": f"口舌是非，{yongshen}受冲，需要谨慎处理",
            "小吉": f"小有收获，{yongshen}平稳，适度发展为宜",
            "空亡": f"虚空无实，{yongshen}失位，事情可能落空"
        }
        return interpretations.get(gong_name, "需要进一步分析")
        
    def _get_related_positions(self, luogong_pos: int) -> List[int]:
        """获取相关宫位"""
        # 返回相邻和对冲宫位
        positions = []
        for i in range(1, 7):
            if i != luogong_pos:
                positions.append(i)
        return positions[:2]  # 返回前两个相关宫位
        
    def _analyze_gong_relation(self, pos1: int, pos2: int) -> str:
        """分析宫位关系"""
        diff = abs(pos1 - pos2)
        if diff == 1 or diff == 5:
            return "相邻"
        elif diff == 3:
            return "对冲"
        else:
            return "相关"
            
    def _calculate_influence(self, gong1: Dict[str, Any], gong2: Dict[str, Any]) -> str:
        """计算宫位影响"""
        wuxing1 = gong1.get("wuxing", "")
        wuxing2 = gong2.get("wuxing", "")
        
        if wuxing1 and wuxing2:
            relation = self.knowledge_base.get_wuxing_relation(wuxing1, wuxing2)
            return f"{wuxing1}与{wuxing2}{relation}"
        return "关系待定"
        
    def _generate_comprehensive_text(self, paipan: PaipanResult, question_type: str, 
                                   gong_analysis: Dict[str, Any], yongshen_list: List[str]) -> str:
        """生成综合解读文本"""
        luogong_analysis = gong_analysis.get("luogong_analysis", {})
        gong_name = luogong_analysis.get("name", "")
        favorable = luogong_analysis.get("favorable", False)
        
        if favorable:
            result_tendency = "整体运势较好"
        else:
            result_tendency = "需要谨慎应对"
            
        return f"关于{question_type}问题，卦象显示{gong_name}，{result_tendency}。" \
               f"用神为{', '.join(yongshen_list)}，{luogong_analysis.get('interpretation', '')}。"
               
    def _generate_detailed_analysis(self, paipan: PaipanResult, question_type: str,
                                  gong_analysis: Dict[str, Any], yongshen_list: List[str]) -> Dict[str, Any]:
        """生成详细分析"""
        return {
            "question_type": question_type,
            "main_yongshen": yongshen_list[0] if yongshen_list else "世爻",
            "luogong_details": gong_analysis.get("luogong_analysis", {}),
            "timeline": self._estimate_timeline(gong_analysis),
            "suggestions": self._generate_suggestions(question_type, gong_analysis)
        }
        
    def _analyze_direction(self, luogong_info: Dict[str, Any], item_desc: str) -> Dict[str, Any]:
        """分析方位"""
        gong_name = luogong_info.get("name", "")
        direction_mapping = {
            "大安": "东北方",
            "留连": "南方", 
            "速喜": "西南方",
            "赤口": "西方",
            "小吉": "东南方",
            "空亡": "北方"
        }
        
        return {
            "primary_direction": direction_mapping.get(gong_name, "正中"),
            "secondary_directions": [direction_mapping.get(gong_name, "正中")],
            "direction_confidence": 0.8 if gong_name in direction_mapping else 0.5
        }
        
    def _generate_location_clues(self, luogong_info: Dict[str, Any], item_desc: str) -> List[str]:
        """生成位置线索"""
        gong_name = luogong_info.get("name", "")
        location_mapping = {
            "大安": ["安静的地方", "卧室", "书房"],
            "留连": ["被遗忘的角落", "储物间", "杂物堆"],
            "速喜": ["显眼的位置", "客厅", "桌面上"],
            "赤口": ["尖锐物品附近", "厨房", "工具箱"],
            "小吉": ["整洁的地方", "抽屉里", "柜子中"],
            "空亡": ["空旷的地方", "可能已遗失", "户外"]
        }
        
        return location_mapping.get(gong_name, ["需要仔细寻找"])
        
    def _estimate_find_time(self, luogong_info: Dict[str, Any]) -> Dict[str, Any]:
        """估计找到时间"""
        gong_name = luogong_info.get("name", "")
        time_mapping = {
            "大安": {"period": "1-3天内", "best_time": "上午"},
            "留连": {"period": "3-7天内", "best_time": "下午"},
            "速喜": {"period": "当天", "best_time": "中午"},
            "赤口": {"period": "2-5天内", "best_time": "傍晚"},
            "小吉": {"period": "1-2天内", "best_time": "上午"},
            "空亡": {"period": "可能找不到", "best_time": "任何时间"}
        }
        
        return time_mapping.get(gong_name, {"period": "未知", "best_time": "任何时间"})
        
    def _calculate_success_probability(self, luogong_info: Dict[str, Any]) -> float:
        """计算成功概率"""
        gong_name = luogong_info.get("name", "")
        probability_mapping = {
            "大安": 0.8,
            "留连": 0.6,
            "速喜": 0.9,
            "赤口": 0.4,
            "小吉": 0.7,
            "空亡": 0.2
        }
        
        return probability_mapping.get(gong_name, 0.5)
        
    def _generate_find_guidance(self, direction_analysis: Dict[str, Any], 
                              location_clues: List[str], time_estimation: Dict[str, Any],
                              success_probability: float) -> str:
        """生成寻物指导"""
        direction = direction_analysis.get("primary_direction", "未知方向")
        period = time_estimation.get("period", "未知时间")
        best_time = time_estimation.get("best_time", "任何时间")
        
        guidance = f"建议在{direction}寻找，重点关注{', '.join(location_clues[:2])}。"
        guidance += f"最佳寻找时间是{best_time}，预计在{period}找到。"
        
        if success_probability > 0.7:
            guidance += "找到的可能性较大，请仔细搜寻。"
        elif success_probability > 0.4:
            guidance += "有一定可能找到，建议扩大搜寻范围。"
        else:
            guidance += "找到的可能性较小，可能需要考虑其他情况。"
            
        return guidance
        
    def _estimate_timeline(self, gong_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """估计时间线"""
        return {
            "short_term": "1-7天",
            "medium_term": "1-3月", 
            "long_term": "3-12月"
        }
        
    def _generate_suggestions(self, question_type: str, gong_analysis: Dict[str, Any]) -> List[str]:
        """生成建议"""
        luogong_analysis = gong_analysis.get("luogong_analysis", {})
        favorable = luogong_analysis.get("favorable", False)
        
        if favorable:
            return [
                "时机有利，可以积极推进",
                "保持现有节奏",
                "注意把握机会"
            ]
        else:
            return [
                "需要谨慎行事",
                "可以考虑延后行动",
                "多听取他人意见"
            ]
