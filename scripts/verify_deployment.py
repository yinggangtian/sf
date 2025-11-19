#!/usr/bin/env python3
"""
部署验证脚本
验证系统部署是否完整，包括数据库、知识库、API 配置等
"""

import sys
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(check_name: str, passed: bool, message: str = ""):
    """打印检查结果"""
    status = "✓ 通过" if passed else "✗ 失败"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    
    print(f"{color}{status}{reset} | {check_name}")
    if message:
        print(f"       {message}")


class DeploymentVerifier:
    """部署验证器"""
    
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, check_name: str, passed: bool, message: str = ""):
        """记录检查结果"""
        self.results.append((check_name, passed, message))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print_result(check_name, passed, message)
    
    def verify_environment_variables(self) -> bool:
        """验证环境变量配置"""
        print_section("1. 环境变量验证")
        
        all_passed = True
        
        # 尝试从配置加载，不强制要求系统环境变量
        from backend.shared.config.settings import get_settings
        settings = get_settings()
        
        required_vars = [
            ("DATABASE_URL", "数据库连接字符串", settings.database_url),
            ("OPENAI_API_KEY", "OpenAI API 密钥", settings.openai_api_key),
        ]
        
        optional_vars = [
            ("REDIS_URL", "Redis 连接字符串（可选）"),
            ("EMBEDDING_MODEL", "嵌入模型名称（默认：text-embedding-3-small）"),
            ("LLM_MODEL", "LLM 模型名称（默认：gpt-4o-mini）"),
        ]
        
        for var_name, description, value in required_vars:
            if value and len(str(value)) > 0:
                # 脱敏显示
                display_value = str(value)[:10] + "..." if len(str(value)) > 10 else str(value)
                source = "系统环境变量" if os.getenv(var_name) else ".env 文件"
                self.add_result(
                    f"配置 {var_name}",
                    True,
                    f"{description} - 已加载 (来源: {source}): {display_value}"
                )
            else:
                self.add_result(
                    f"配置 {var_name}",
                    False,
                    f"{description} - 未配置"
                )
                all_passed = False
        
        optional_vars = [
            ("REDIS_URL", "Redis 连接字符串（可选）", getattr(settings, 'redis_url', None)),
            ("EMBEDDING_MODEL", "嵌入模型名称", settings.embedding_model),
            ("OPENAI_MODEL", "OpenAI 模型名称", settings.openai_model),
        ]
        
        # 检查可选变量
        for var_name, description, value in optional_vars:
            if value:
                display_value = str(value)[:20] + "..." if len(str(value)) > 20 else str(value)
                self.add_result(
                    f"配置 {var_name} (可选)",
                    True,
                    f"{description} - {display_value}"
                )
        
        return all_passed
    
    def verify_database_connection(self) -> bool:
        """验证数据库连接"""
        print_section("2. 数据库连接验证")
        
        try:
            from sqlalchemy import create_engine, text
            from backend.shared.config.settings import get_settings
            
            settings = get_settings()
            engine = create_engine(settings.database_url)
            
            # 测试连接
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                
            self.add_result(
                "数据库连接",
                True,
                f"成功连接到 PostgreSQL: {version[:50]}"
            )
            
            # 检查 pgvector 扩展（可选，当前使用模拟数据）
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
                    has_vector = result.fetchone() is not None
                
                if has_vector:
                    self.add_result(
                        "pgvector 扩展 (可选)",
                        True,
                        "pgvector 扩展已安装"
                    )
                else:
                    # 不标记为失败，因为当前使用模拟数据
                    print("  ⚠️  提示 | pgvector 扩展")
                    print("       pgvector 扩展未安装（当前使用模拟 RAG 数据，生产环境建议安装）")
            except Exception as e:
                self.add_result(
                    "pgvector 扩展",
                    False,
                    f"检查失败: {str(e)}"
                )
            
            return True
            
        except Exception as e:
            self.add_result(
                "数据库连接",
                False,
                f"连接失败: {str(e)}"
            )
            return False
    
    def verify_database_tables(self) -> bool:
        """验证数据库表结构"""
        print_section("3. 数据库表结构验证")
        
        try:
            from sqlalchemy import create_engine, inspect
            from backend.shared.config.settings import get_settings
            
            settings = get_settings()
            engine = create_engine(settings.database_url)
            inspector = inspect(engine)
            
            required_tables = [
                ("users", "用户表"),
                ("user_profiles", "用户画像表"),
                ("divination_records", "占卜记录表"),
                ("liu_gong", "六宫数据表"),
                ("liu_shou", "六兽数据表"),
                ("liu_qin", "六亲数据表"),
                ("di_zhi", "地支数据表"),
            ]
            
            all_passed = True
            for table_name, description in required_tables:
                if table_name in inspector.get_table_names():
                    self.add_result(
                        f"数据表 {table_name}",
                        True,
                        f"{description} - 存在"
                    )
                else:
                    self.add_result(
                        f"数据表 {table_name}",
                        False,
                        f"{description} - 不存在（需要运行数据库迁移）"
                    )
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.add_result(
                "数据库表结构检查",
                False,
                f"检查失败: {str(e)}"
            )
            return False
    
    def verify_knowledge_base(self) -> bool:
        """验证知识库数据"""
        print_section("4. 知识库数据验证")
        
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from backend.shared.config.settings import get_settings
            from backend.shared.db.models.knowledge import Gong, Shou, Qin, DiZhi
            
            settings = get_settings()
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            try:
                # 检查六宫数据
                gong_count = db.query(Gong).count()
                if gong_count >= 6:
                    self.add_result(
                        "六宫数据",
                        True,
                        f"已加载 {gong_count} 条记录（至少需要 6 条）"
                    )
                else:
                    self.add_result(
                        "六宫数据",
                        False,
                        f"仅有 {gong_count} 条记录（至少需要 6 条）"
                    )
                
                # 检查六兽数据
                shou_count = db.query(Shou).count()
                if shou_count >= 6:
                    self.add_result(
                        "六兽数据",
                        True,
                        f"已加载 {shou_count} 条记录"
                    )
                else:
                    self.add_result(
                        "六兽数据",
                        False,
                        f"仅有 {shou_count} 条记录（至少需要 6 条）"
                    )
                
                # 检查六亲数据
                qin_count = db.query(Qin).count()
                if qin_count >= 5:
                    self.add_result(
                        "六亲数据",
                        True,
                        f"已加载 {qin_count} 条记录"
                    )
                else:
                    self.add_result(
                        "六亲数据",
                        False,
                        f"仅有 {qin_count} 条记录（至少需要 5 条）"
                    )
                
                # 检查地支数据
                dizhi_count = db.query(DiZhi).count()
                if dizhi_count >= 12:
                    self.add_result(
                        "地支数据",
                        True,
                        f"已加载 {dizhi_count} 条记录"
                    )
                else:
                    self.add_result(
                        "地支数据",
                        False,
                        f"仅有 {dizhi_count} 条记录（至少需要 12 条）"
                    )
                
                return gong_count >= 6 and shou_count >= 6
                
            finally:
                db.close()
                
        except Exception as e:
            self.add_result(
                "知识库数据检查",
                False,
                f"检查失败: {str(e)}"
            )
            return False
    
    def verify_openai_api(self) -> bool:
        """验证 OpenAI API 连接"""
        print_section("5. OpenAI API 验证")
        
        try:
            import openai
            from backend.shared.config.settings import get_settings
            
            settings = get_settings()
            
            # 设置 API Key
            if not settings.openai_api_key:
                self.add_result(
                    "OpenAI API Key",
                    False,
                    "未设置 OPENAI_API_KEY 环境变量"
                )
                return False
            
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            # 测试简单的 API 调用
            response = client.chat.completions.create(
                model=settings.openai_model or "gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            self.add_result(
                "OpenAI API 连接",
                True,
                f"成功调用 {settings.openai_model or 'gpt-4o'} 模型"
            )
            
            # 测试嵌入模型
            try:
                embedding_response = client.embeddings.create(
                    model=settings.embedding_model or "text-embedding-3-large",
                    input="测试文本"
                )
                
                self.add_result(
                    "OpenAI Embedding API",
                    True,
                    f"成功调用 {settings.embedding_model or 'text-embedding-3-large'} 模型"
                )
            except Exception as e:
                self.add_result(
                    "OpenAI Embedding API",
                    False,
                    f"嵌入模型调用失败: {str(e)}"
                )
            
            return True
            
        except Exception as e:
            self.add_result(
                "OpenAI API 连接",
                False,
                f"API 调用失败: {str(e)}"
            )
            return False
    
    def verify_application_startup(self) -> bool:
        """验证应用程序启动"""
        print_section("6. 应用程序启动验证")
        
        try:
            from app.main import app
            
            self.add_result(
                "FastAPI 应用初始化",
                True,
                "应用程序成功导入"
            )
            
            # 检查路由
            routes = [route.path for route in app.routes]
            required_routes = ["/ai/divination", "/health"]
            
            for route in required_routes:
                if any(route in r for r in routes):
                    self.add_result(
                        f"路由 {route}",
                        True,
                        "路由已注册"
                    )
                else:
                    self.add_result(
                        f"路由 {route}",
                        False,
                        "路由未找到"
                    )
            
            return True
            
        except Exception as e:
            self.add_result(
                "应用程序启动",
                False,
                f"启动失败: {str(e)}"
            )
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有验证检查"""
        print(f"\n{'#'*60}")
        print(f"#  部署验证 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}\n")
        
        # 执行所有检查
        self.verify_environment_variables()
        self.verify_database_connection()
        self.verify_database_tables()
        self.verify_knowledge_base()
        self.verify_openai_api()
        self.verify_application_startup()
        
        # 打印总结
        print_section("验证总结")
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"总检查项: {total}")
        print(f"✓ 通过: {self.passed}")
        print(f"✗ 失败: {self.failed}")
        print(f"成功率: {success_rate:.1f}%\n")
        
        if self.failed == 0:
            print("\033[92m✓ 所有检查通过！系统部署完整。\033[0m\n")
            return {"status": "success", "passed": self.passed, "failed": self.failed}
        else:
            print(f"\033[91m✗ 有 {self.failed} 项检查失败，请修复后重新验证。\033[0m\n")
            
            # 打印失败的检查项
            print("失败的检查项：")
            for check_name, passed, message in self.results:
                if not passed:
                    print(f"  - {check_name}: {message}")
            print()
            
            return {"status": "failed", "passed": self.passed, "failed": self.failed}


def main():
    """主函数"""
    verifier = DeploymentVerifier()
    result = verifier.run_all_checks()
    
    # 返回适当的退出码
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
