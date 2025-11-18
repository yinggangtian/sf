"""
算法适配器基类
定义统一的算法接口，实现插件式算法扩展
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class AlgorithmAdapter(ABC):
    """
    算法适配器抽象基类
    
    所有玄学算法适配器都应继承此类并实现其抽象方法
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取算法名称
        
        Returns:
            算法名称标识符 (如: "xlr-liuren", "xlr-bazhi")
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取算法描述
        
        Returns:
            算法的详细描述信息
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行算法计算
        
        Args:
            inputs: 输入参数字典，必须先通过 validate_input() 验证
            
        Returns:
            算法计算结果字典
            
        Raises:
            RuntimeError: 算法执行失败时抛出
        """
        pass
    
    def get_required_inputs(self) -> list[str]:
        """
        获取必需的输入参数名称列表
        
        Returns:
            必需参数名称列表
        """
        return []
    
    def get_optional_inputs(self) -> list[str]:
        """
        获取可选的输入参数名称列表
        
        Returns:
            可选参数名称列表
        """
        return []
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        获取输出数据结构描述
        
        Returns:
            输出schema描述字典
        """
        return {}
