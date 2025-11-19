#!/usr/bin/env python3
"""
配置验证脚本
验证所有配置项正确加载，不暴露敏感信息
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def mask_sensitive(value: str, show_chars: int = 4) -> str:
    """脱敏处理敏感值"""
    if not value or len(value) <= show_chars:
        return "***"
    return f"{value[:show_chars]}{'*' * (len(value) - show_chars)}"


def validate_config():
    """验证配置加载"""
    print("=" * 60)
    print("配置验证开始")
    print("=" * 60)
    
    try:
        # 导入配置
        from backend.shared.config.settings import settings
        
        print("\n✅ 配置模块导入成功\n")
        
        # 应用配置
        print("【应用配置】")
        print(f"  APP_NAME: {settings.app_name}")
        print(f"  ENVIRONMENT: {settings.environment}")
        print(f"  DEBUG: {settings.debug}")
        
        # 数据库配置
        print("\n【数据库配置】")
        print(f"  DB_HOST: {settings.db_host}")
        print(f"  DB_PORT: {settings.db_port}")
        print(f"  DB_NAME: {settings.db_name}")
        print(f"  DB_USER: {settings.db_user}")
        if settings.db_password:
            print(f"  DB_PASSWORD: {mask_sensitive(settings.db_password)}")
        else:
            print("  DB_PASSWORD: (empty)")
        # 显示连接URL（脱敏）
        db_url = settings.database_url
        if '@' in db_url and settings.db_password:
            masked_url = db_url.replace(settings.db_password, mask_sensitive(settings.db_password))
            print(f"  DATABASE_URL: {masked_url}")
        else:
            print(f"  DATABASE_URL: {db_url}")
        
        # Redis 配置
        print("\n【Redis 配置】")
        print(f"  REDIS_HOST: {settings.redis_host}")
        print(f"  REDIS_PORT: {settings.redis_port}")
        print(f"  REDIS_DB: {settings.redis_db}")
        if settings.redis_password:
            print(f"  REDIS_PASSWORD: {mask_sensitive(settings.redis_password)}")
        else:
            print("  REDIS_PASSWORD: (empty)")
        print(f"  REDIS_URL: {settings.redis_url}")
        print(f"  ENABLE_CACHE: {settings.enable_cache}")
        print(f"  KB_CACHE_TTL: {settings.kb_cache_ttl}s")
        print(f"  USER_CACHE_TTL: {settings.user_cache_ttl}s")
        
        # OpenAI 配置
        print("\n【OpenAI 配置】")
        if settings.openai_api_key:
            print(f"  OPENAI_API_KEY: {mask_sensitive(settings.openai_api_key, 7)}")
        else:
            print("  OPENAI_API_KEY: (empty)")
        print(f"  OPENAI_MODEL: {settings.openai_model}")
        print(f"  OPENAI_TEMPERATURE: {settings.openai_temperature}")
        print(f"  OPENAI_TIMEOUT: {settings.openai_timeout}s")
        
        # RAG 配置
        print("\n【RAG 配置】")
        print(f"  EMBEDDING_MODEL: {settings.embedding_model}")
        print(f"  RAG_TOP_K: {settings.rag_top_k}")
        print(f"  RAG_SCORE_THRESHOLD: {settings.rag_score_threshold}")
        print(f"  RAG_TIMEOUT: {settings.rag_timeout}s")
        
        # JWT 配置
        print("\n【JWT 配置】")
        print(f"  JWT_SECRET_KEY: {mask_sensitive(settings.jwt_secret_key)}")
        print(f"  JWT_ALGORITHM: {settings.jwt_algorithm}")
        print(f"  JWT_EXPIRE_MINUTES: {settings.jwt_expire_minutes}")
        
        # 业务配置
        print("\n【业务配置】")
        print(f"  VALID_NUMBERS: {settings.valid_numbers}")
        print(f"  VALID_QUESTION_TYPES: {settings.valid_question_types}")
        print(f"  VALID_GENDERS: {settings.valid_genders}")
        print(f"  DEFAULT_QUESTION_TYPE: {settings.default_question_type}")
        print(f"  MAX_ITEM_DESCRIPTION_LENGTH: {settings.max_item_description_length}")
        print(f"  MAX_RECORDS_PER_USER: {settings.max_records_per_user}")
        print(f"  DEFAULT_PAGE_SIZE: {settings.default_page_size}")
        print(f"  MAX_PAGE_SIZE: {settings.max_page_size}")
        
        # 日志配置
        print("\n【日志配置】")
        print(f"  LOG_LEVEL: {settings.log_level}")
        print(f"  LOG_FORMAT: {settings.log_format}")
        print(f"  LOG_FILE: {settings.log_file or '(console only)'}")
        print(f"  ENABLE_LOGGING: {settings.enable_logging}")
        
        # 监控配置
        print("\n【监控配置】")
        print(f"  ENABLE_METRICS: {settings.enable_metrics}")
        print(f"  ENABLE_TRACING: {settings.enable_tracing}")
        
        # Celery 配置
        print("\n【Celery 配置】")
        print(f"  CELERY_BROKER_URL: {settings.celery_broker_url}")
        print(f"  CELERY_RESULT_BACKEND: {settings.celery_result_backend}")
        
        # CORS 配置
        print("\n【CORS 配置】")
        print(f"  CORS_ORIGINS: {settings.cors_origins}")
        print(f"  CORS_ALLOW_CREDENTIALS: {settings.cors_allow_credentials}")
        
        # AWS 配置
        print("\n【AWS/Serverless 配置】")
        print(f"  AWS_REGION: {settings.aws_region}")
        print(f"  LAMBDA_TIMEOUT: {settings.lambda_timeout}s")
        print(f"  LAMBDA_MEMORY: {settings.lambda_memory}MB")
        
        print("\n" + "=" * 60)
        print("✅ 配置验证完成 - 所有配置项已正确加载")
        print("=" * 60)
        
        # 检查关键配置
        print("\n【关键配置检查】")
        warnings = []
        
        if not settings.db_host or not settings.db_name or not settings.db_user:
            warnings.append("⚠️  数据库配置不完整")
        
        if not settings.openai_api_key:
            warnings.append("⚠️  OPENAI_API_KEY 未设置")
        
        if settings.jwt_secret_key in ['your-secret-key-here', 'your-secret-key-change-this-in-production']:
            warnings.append("⚠️  JWT_SECRET_KEY 使用默认值，生产环境请修改")
        
        if settings.environment == 'production':
            if settings.debug:
                warnings.append("⚠️  生产环境不应启用 DEBUG 模式")
            if not settings.db_password:
                warnings.append("⚠️  生产环境应设置数据库密码")
        
        if warnings:
            print("\n警告：")
            for warning in warnings:
                print(f"  {warning}")
        else:
            print("  ✅ 所有关键配置已正确设置")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ 导入配置失败: {e}")
        print("\n请确保：")
        print("  1. 已创建 .env 文件（可从 .env.example 复制）")
        print("  2. backend/shared/config/settings.py 存在")
        print("  3. 已安装所有依赖: pip install -r requirements.txt")
        return False
        
    except (ValueError, AttributeError, RuntimeError) as e:  # noqa: BLE001
        print(f"\n❌ 配置验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
