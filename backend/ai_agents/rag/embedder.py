"""嵌入生成器
使用 OpenAI Embedding API 生成文本向量
"""

from typing import List, Optional
import openai
from backend.shared.config.settings import get_settings


class Embedder:
    """OpenAI 嵌入生成器"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        """
        初始化嵌入生成器
        
        Args:
            api_key: OpenAI API 密钥（可选，默认从配置读取）
            model: 嵌入模型名称
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        
    def embed_text(self, text: str) -> List[float]:
        """
        为单个文本生成嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量列表
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表的列表
        """
        if not texts:
            return []
        
        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("至少需要一个非空文本")
        
        response = self.client.embeddings.create(
            model=self.model,
            input=valid_texts
        )
        
        return [item.embedding for item in response.data]
