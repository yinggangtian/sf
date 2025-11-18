"""
应用配置 - 基于 Pydantic Settings
整合 XLR 配置和通用配置
"""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    # ==================== 基础配置 ====================
    app_name: str = Field(default="玄学大师AI Agent", description="应用名称")
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=True, description="调试模式")
    
    # ==================== 数据库配置 ====================
    db_host: str = Field(default="localhost", description="数据库主机")
    db_port: int = Field(default=5432, description="数据库端口")
    db_name: str = Field(default="xiaoliuren", description="数据库名称")
    db_user: str = Field(default="postgres", description="数据库用户")
    db_password: str = Field(default="", description="数据库密码")
    db_pool_size: int = Field(default=10, description="数据库连接池大小")
    db_max_overflow: int = Field(default=20, description="连接池最大溢出")
    db_echo: bool = Field(default=False, description="是否输出SQL日志")
    
    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # ==================== Redis 缓存配置 ====================
    redis_host: str = Field(default="localhost", description="Redis主机")
    redis_port: int = Field(default=6379, description="Redis端口")
    redis_db: int = Field(default=0, description="Redis数据库编号")
    redis_password: Optional[str] = Field(default=None, description="Redis密码")
    redis_timeout: int = Field(default=5, description="Redis超时(秒)")
    
    @property
    def redis_url(self) -> str:
        """Redis连接URL"""
        password_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{password_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # ==================== 缓存 TTL 配置 ====================
    kb_cache_ttl: int = Field(default=3600, description="知识库缓存TTL(秒)")
    user_cache_ttl: int = Field(default=1800, description="用户会话缓存TTL(秒)")
    api_cache_ttl: int = Field(default=300, description="API响应缓存TTL(秒)")
    enable_cache: bool = Field(default=True, description="是否启用缓存")
    
    # ==================== OpenAI 配置 ====================
    openai_api_key: str = Field(default="", description="OpenAI API密钥")
    openai_model: str = Field(default="gpt-4o", description="OpenAI模型")
    openai_temperature: float = Field(default=0.7, description="温度参数")
    openai_timeout: int = Field(default=30, description="请求超时(秒)")
    
    # ==================== RAG 配置 ====================
    embedding_model: str = Field(default="text-embedding-3-large", description="向量化模型")
    rag_top_k: int = Field(default=5, description="RAG检索Top-K")
    rag_score_threshold: float = Field(default=0.7, description="RAG相似度阈值")
    rag_timeout: int = Field(default=10, description="RAG检索超时(秒)")
    
    # ==================== JWT 认证配置 ====================
    jwt_secret_key: str = Field(default="your-secret-key-here", description="JWT密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_expire_minutes: int = Field(default=1440, description="JWT过期时间(分钟)")
    
    # ==================== Celery 配置 ====================
    celery_broker_url: str = Field(default="redis://localhost:6379/0", description="Celery Broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", description="Celery结果后端")
    
    # ==================== 日志配置 ====================
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="json", description="日志格式(json/text)")
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    enable_logging: bool = Field(default=True, description="是否启用日志")
    
    # ==================== 监控配置 ====================
    enable_metrics: bool = Field(default=False, description="是否启用指标采集")
    enable_tracing: bool = Field(default=False, description="是否启用链路追踪")
    
    # ==================== 业务配置 ====================
    valid_numbers: List[int] = Field(default=[1, 2, 3, 4, 5, 6], description="有效报数范围")
    valid_question_types: List[str] = Field(
        default=["事业", "财运", "感情", "健康", "学业", "出行", "官司", "寻物", "通用"],
        description="有效问题类型"
    )
    valid_genders: List[str] = Field(default=["男", "女"], description="有效性别")
    default_question_type: str = Field(default="通用", description="默认问题类型")
    max_item_description_length: int = Field(default=200, description="寻物描述最大长度")
    max_records_per_user: int = Field(default=1000, description="用户最大记录数")
    
    # ==================== API 配置 ====================
    api_rate_limit: int = Field(default=100, description="API速率限制(请求/分钟)")
    default_page_size: int = Field(default=10, description="默认分页大小")
    max_page_size: int = Field(default=100, description="最大分页大小")
    
    # ==================== CORS 配置 ====================
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="允许的跨域来源"
    )
    cors_allow_credentials: bool = Field(default=True, description="允许携带凭证")
    
    # ==================== AWS/Serverless 配置 ====================
    aws_region: str = Field(default="us-east-1", description="AWS区域")
    lambda_timeout: int = Field(default=30, description="Lambda超时(秒)")
    lambda_memory: int = Field(default=512, description="Lambda内存(MB)")
    
    # ==================== 辅助方法 ====================
    
    @property
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.environment.lower() == "production"
    
    @property
    def is_test(self) -> bool:
        """判断是否为测试环境"""
        return self.environment.lower() == "test"


# ==================== 配置实例 ====================

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例(单例模式)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# 便捷导出
settings = get_settings()
