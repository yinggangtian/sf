"""
小六壬占卜工具
提供给 Agent 调用的工具封装
"""

from typing import Dict, Any, Optional
from datetime import datetime

from ..services.divination_service import DivinationService
from ..services.interpretation_service import InterpretationService
from ..xlr.schemas import QiguaRequest, PaipanResult


class LiurenTool:
    """小六壬占卜工具类"""
    
    def __init__(
        self, 
        divination_service: DivinationService,
        interpretation_service: InterpretationService
    ):
        """
        初始化小六壬工具
        
        Args:
            divination_service: 占卜服务实例
            interpretation_service: 解卦服务实例
        """
        self.divination_service = divination_service
        self.interpretation_service = interpretation_service
    
    def qigua(
        self,
        number1: int,
        number2: int,
        question_type: Optional[str] = None,
        gender: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        起卦操作
        
        Args:
            number1: 第一个报数(1-6)
            number2: 第二个报数(1-6)
            question_type: 问题类型(可选)
            gender: 性别(可选)
            user_id: 用户ID(可选)
            
        Returns:
            起卦结果字典，包含排盘信息
            
        Raises:
            ValueError: 参数验证失败
        """
        # 构建请求
        request = QiguaRequest(
            number1=number1,
            number2=number2,
            qigua_time=datetime.now(),
            question_type=question_type,
            gender=gender,
            user_id=user_id
        )
        
        # 执行起卦
        paipan_result = self.divination_service.process_qigua(
            request, 
            save_record=bool(user_id)
        )
        
        # 返回简化结果
        return {
            "success": True,
            "luogong": paipan_result.qigua_info.luogong,
            "luogong_name": self._get_luogong_name(paipan_result),
            "shichen": paipan_result.qigua_info.shichen_info.get("dizhi", ""),
            "paipan_summary": self._generate_paipan_summary(paipan_result),
            "full_result": paipan_result.model_dump()
        }
    
    def jiegua(
        self,
        paipan_result: Dict[str, Any],
        question_type: str,
        gender: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        解卦操作
        
        Args:
            paipan_result: 排盘结果(来自qigua)
            question_type: 问题类型
            gender: 性别
            user_id: 用户ID(可选)
            
        Returns:
            解卦结果字典，包含综合解读
            
        Raises:
            ValueError: 参数验证失败
        """
        # 转换为 PaipanResult 对象
        paipan_obj = PaipanResult(**paipan_result)
        
        # 执行解卦
        interpretation_result = self.interpretation_service.process_jiegua(
            paipan_result=paipan_obj,
            question_type=question_type,
            gender=gender,
            user_id=user_id,
            save_to_record=bool(user_id)
        )
        
        # 返回结果
        return {
            "success": True,
            "yongshen": interpretation_result.yongshen,
            "comprehensive_interpretation": interpretation_result.comprehensive_interpretation,
            "favorable": interpretation_result.gong_analysis.get("luogong_analysis", {}).get("favorable", False),
            "suggestions": interpretation_result.detailed_analysis.get("suggestions", []),
            "full_result": interpretation_result.model_dump()
        }
    
    def find_object(
        self,
        paipan_result: Dict[str, Any],
        item_description: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        寻物操作
        
        Args:
            paipan_result: 排盘结果(来自qigua)
            item_description: 物品描述
            user_id: 用户ID(可选)
            
        Returns:
            寻物结果字典，包含方位和时间信息
            
        Raises:
            ValueError: 参数验证失败
        """
        # 转换为 PaipanResult 对象
        paipan_obj = PaipanResult(**paipan_result)
        
        # 执行寻物分析
        find_result = self.interpretation_service.process_find_object(
            paipan_result=paipan_obj,
            item_description=item_description,
            user_id=user_id,
            save_record=bool(user_id)
        )
        
        # 返回结果
        return {
            "success": True,
            "direction": find_result.direction_analysis.get("primary_direction", "未知"),
            "location_clues": find_result.location_clues[:3],  # 返回前3条线索
            "time_estimate": find_result.time_estimation.get("period", "未知"),
            "success_probability": find_result.success_probability,
            "guidance": find_result.detailed_guidance,
            "full_result": find_result.model_dump()
        }
    
    def qigua_and_jiegua(
        self,
        number1: int,
        number2: int,
        question_type: str,
        gender: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        一站式起卦+解卦
        
        Args:
            number1: 第一个报数(1-6)
            number2: 第二个报数(1-6)
            question_type: 问题类型
            gender: 性别
            user_id: 用户ID(可选)
            
        Returns:
            完整的起卦和解卦结果
        """
        # 先起卦
        qigua_result = self.qigua(number1, number2, question_type, gender, user_id)
        
        # 再解卦
        jiegua_result = self.jiegua(
            qigua_result["full_result"],
            question_type,
            gender,
            user_id
        )
        
        # 合并结果
        return {
            "success": True,
            "qigua": {
                "luogong": qigua_result["luogong"],
                "luogong_name": qigua_result["luogong_name"],
                "shichen": qigua_result["shichen"],
                "paipan_summary": qigua_result["paipan_summary"]
            },
            "jiegua": {
                "yongshen": jiegua_result["yongshen"],
                "interpretation": jiegua_result["comprehensive_interpretation"],
                "favorable": jiegua_result["favorable"],
                "suggestions": jiegua_result["suggestions"]
            }
        }
    
    # ==================== 内部辅助方法 ====================
    
    def _get_luogong_name(self, paipan_result: PaipanResult) -> str:
        """获取落宫名称"""
        luogong_pos = paipan_result.qigua_info.luogong
        luogong_info = paipan_result.paipan_data.get("liugong", {}).get(f"gong_{luogong_pos}", {})
        return luogong_info.get("name", "未知")
    
    def _generate_paipan_summary(self, paipan_result: PaipanResult) -> str:
        """生成排盘摘要"""
        luogong_name = self._get_luogong_name(paipan_result)
        shichen = paipan_result.qigua_info.shichen_info.get("dizhi", "")
        
        return f"落宫为{luogong_name}，时辰为{shichen}时"
