"""
小六壬算法适配器
包装 PaipanEngine 和 JieguaEngine，提供统一接口
"""

from datetime import datetime
from typing import Dict, Any
from .base import AlgorithmAdapter
from ..liuren.engine import PaipanEngine
from ..liuren.jiegua_engine import JieguaEngine
from ..liuren.utils import KnowledgeBase
from ..schemas import QiguaRequest, QiguaInfo, JieguaRequest, FindObjectRequest


class LiurenAdapter(AlgorithmAdapter):
    """小六壬算法适配器"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """
        初始化小六壬适配器
        
        Args:
            knowledge_base: 知识库实例
        """
        self.knowledge_base = knowledge_base
        self.paipan_engine = PaipanEngine(knowledge_base)
        self.jiegua_engine = JieguaEngine(knowledge_base)
        
    def get_name(self) -> str:
        """获取算法名称"""
        return "xlr-liuren"
    
    def get_description(self) -> str:
        """获取算法描述"""
        return "小六壬占卜算法，支持起卦、排盘、解卦和寻物专项分析"
    
    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        """
        验证输入参数
        
        Args:
            inputs: 输入参数字典
            
        Returns:
            验证是否通过
            
        Raises:
            ValueError: 输入参数不合法时抛出
        """
        operation = inputs.get("operation")
        
        if operation not in ["qigua", "jiegua", "find_object"]:
            raise ValueError(f"不支持的操作类型: {operation}，支持: qigua, jiegua, find_object")
        
        if operation == "qigua":
            # 验证起卦参数
            if "number1" not in inputs or "number2" not in inputs:
                raise ValueError("起卦需要 number1 和 number2 参数")
            
            num1, num2 = inputs["number1"], inputs["number2"]
            if not (1 <= num1 <= 6 and 1 <= num2 <= 6):
                raise ValueError("报数必须在 1-6 之间")
                
            # qigua_time 可选，默认当前时间
            if "qigua_time" in inputs:
                if not isinstance(inputs["qigua_time"], (datetime, str)):
                    raise ValueError("qigua_time 必须是 datetime 或 ISO格式字符串")
        
        elif operation == "jiegua":
            # 验证解卦参数
            if "paipan_result" not in inputs:
                raise ValueError("解卦需要 paipan_result 参数")
            if "question_type" not in inputs or "gender" not in inputs:
                raise ValueError("解卦需要 question_type 和 gender 参数")
        
        elif operation == "find_object":
            # 验证寻物参数
            if "paipan_result" not in inputs:
                raise ValueError("寻物需要 paipan_result 参数")
            if "item_description" not in inputs:
                raise ValueError("寻物需要 item_description 参数")
        
        return True
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行算法计算
        
        Args:
            inputs: 输入参数字典
            
        Returns:
            算法计算结果字典
            
        Raises:
            RuntimeError: 算法执行失败时抛出
        """
        # 先验证输入
        self.validate_input(inputs)
        
        operation = inputs["operation"]
        
        try:
            if operation == "qigua":
                return self._run_qigua(inputs)
            elif operation == "jiegua":
                return self._run_jiegua(inputs)
            elif operation == "find_object":
                return self._run_find_object(inputs)
        except Exception as e:
            raise RuntimeError(f"算法执行失败: {str(e)}") from e
    
    def get_required_inputs(self) -> list[str]:
        """获取必需的输入参数名称列表"""
        return ["operation"]
    
    def get_optional_inputs(self) -> list[str]:
        """获取可选的输入参数名称列表"""
        return ["user_id", "qigua_time", "question_type", "gender"]
    
    def get_output_schema(self) -> Dict[str, Any]:
        """获取输出数据结构描述"""
        return {
            "qigua": {
                "paipan_result": "PaipanResult object",
                "description": "完整的排盘结果，包含起卦信息和六宫六兽排盘"
            },
            "jiegua": {
                "interpretation_result": "InterpretationResult object",
                "description": "解卦结果，包含用神分析、宫位分析和综合解读"
            },
            "find_object": {
                "find_object_result": "FindObjectResult object",
                "description": "寻物结果，包含方位分析、位置线索和时间估计"
            }
        }
    
    # ==================== 内部方法 ====================
    
    def _run_qigua(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行起卦操作"""
        num1 = inputs["number1"]
        num2 = inputs["number2"]
        qigua_time = inputs.get("qigua_time", datetime.now())
        
        # 如果 qigua_time 是字符串，转换为 datetime
        if isinstance(qigua_time, str):
            qigua_time = datetime.fromisoformat(qigua_time)
        
        # 计算落宫
        luogong = self.paipan_engine.calculate_luogong(num1, num2)
        
        # 获取时辰信息
        shichen_info = self.paipan_engine.get_shichen_info(qigua_time)
        
        # 构建起卦信息
        qigua_info = QiguaInfo(
            number1=num1,
            number2=num2,
            qigua_time=qigua_time,
            luogong=luogong,
            shichen_info=shichen_info
        )
        
        # 生成完整排盘
        paipan_result = self.paipan_engine.generate_paipan(qigua_info)
        
        return {
            "operation": "qigua",
            "success": True,
            "paipan_result": paipan_result.model_dump(),
            "luogong": luogong,
            "shichen": shichen_info.get("dizhi", "")
        }
    
    def _run_jiegua(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行解卦操作"""
        # 从 inputs 重构 PaipanResult
        paipan_data = inputs["paipan_result"]
        
        # 如果是字典，需要转换为 PaipanResult 对象
        if isinstance(paipan_data, dict):
            from ..schemas import PaipanResult
            paipan_result = PaipanResult(**paipan_data)
        else:
            paipan_result = paipan_data
        
        question_type = inputs["question_type"]
        gender = inputs["gender"]
        
        # 执行解卦
        interpretation_result = self.jiegua_engine.generate_interpretation(
            paipan_result, question_type, gender
        )
        
        return {
            "operation": "jiegua",
            "success": True,
            "interpretation_result": interpretation_result.model_dump(),
            "question_type": question_type,
            "yongshen": interpretation_result.yongshen,
            "comprehensive_text": interpretation_result.comprehensive_interpretation
        }
    
    def _run_find_object(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行寻物操作"""
        # 从 inputs 重构 PaipanResult
        paipan_data = inputs["paipan_result"]
        
        # 如果是字典，需要转换为 PaipanResult 对象
        if isinstance(paipan_data, dict):
            from ..schemas import PaipanResult
            paipan_result = PaipanResult(**paipan_data)
        else:
            paipan_result = paipan_data
        
        item_description = inputs["item_description"]
        
        # 执行寻物分析
        find_object_result = self.jiegua_engine.analyze_find_object(
            paipan_result, item_description
        )
        
        return {
            "operation": "find_object",
            "success": True,
            "find_object_result": find_object_result.model_dump(),
            "item_description": item_description,
            "direction": find_object_result.direction_analysis.get("primary_direction", ""),
            "success_probability": find_object_result.success_probability
        }
