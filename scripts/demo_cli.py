#!/usr/bin/env python3
"""
占卜系统命令行测试工具
用于测试完整的占卜流程

使用方法:
    uv run python scripts/demo_cli.py

示例输入:
    8, 6, 男, 想问一下我明年爱情怎么样
    或者 8 6 男 明年爱情
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from backend.shared.db.session import SessionLocal
from backend.shared.db.models.knowledge import Gong, Shou, Qin, DiZhi
from backend.ai_agents.agents.master_agent import MasterAgent
from backend.ai_agents.agents.orchestrator import OrchestratorAgent
from backend.ai_agents.agents.explainer import ExplainerAgent
from backend.ai_agents.services.divination_service import DivinationService
from backend.ai_agents.services.rag_service import RAGService
from backend.ai_agents.services.memory_service import MemoryService
from backend.ai_agents.xlr.adapters.liuren_adapter import LiurenAdapter
from backend.ai_agents.xlr.liuren.utils import KnowledgeBase
from backend.ai_agents.rag.retriever import Retriever
from backend.ai_agents.rag.embedder import Embedder


def initialize_master_agent(db_session: Session) -> MasterAgent:
    """初始化 MasterAgent"""
    print("🔧 初始化占卜系统...")
    
    # 加载知识库数据
    kb = KnowledgeBase()
    gong_list = db_session.query(Gong).order_by(Gong.position).all()
    shou_list = db_session.query(Shou).order_by(Shou.position).all()
    qin_list = db_session.query(Qin).all()
    dizhi_list = db_session.query(DiZhi).all()
    
    kb.load_gong_data(gong_list)
    kb.load_shou_data(shou_list)
    kb.load_qin_data(qin_list)
    kb.load_dizhi_data(dizhi_list)
    
    print(f"  ✓ 加载知识库: 宫({len(gong_list)}) 兽({len(shou_list)}) 亲({len(qin_list)}) 地支({len(dizhi_list)})")
    
    # 创建各个服务
    liuren_adapter = LiurenAdapter(knowledge_base=kb)
    divination_service = DivinationService(
        liuren_adapter=liuren_adapter,
        db_session=db_session
    )
    
    embedder = Embedder()
    retriever = Retriever(embedder=embedder)
    rag_service = RAGService(
        retriever=retriever,
        db_session=db_session
    )
    
    memory_service = MemoryService(db_session=db_session)
    orchestrator = OrchestratorAgent()
    explainer = ExplainerAgent()
    
    master_agent = MasterAgent(
        orchestrator=orchestrator,
        explainer=explainer,
        divination_service=divination_service,
        rag_service=rag_service,
        memory_service=memory_service,
        tool_timeout=30.0
    )
    
    print("  ✓ MasterAgent 初始化完成\n")
    return master_agent


def process_query(master_agent: MasterAgent, user_id: int, query: str):
    """处理用户查询"""
    print(f"📝 用户输入: {query}")
    print("-" * 60)
    
    try:
        # 调用 MasterAgent
        result = master_agent.run(
            user_message=query,
            user_id=user_id,
            session_id=f"cli_session_{user_id}"
        )
        
        print("\n📊 系统响应:")
        print("=" * 60)
        print(result["reply"])
        print("=" * 60)
        
        # 显示额外信息
        if "metadata" in result:
            print("\n🔍 元数据:")
            metadata = result["metadata"]
            if "reasoning" in metadata:
                print(f"  推理过程: {metadata['reasoning']}")
            if "confidence" in metadata:
                print(f"  置信度: {metadata['confidence']}")
            if "divination_id" in metadata:
                print(f"  占卜记录ID: {metadata['divination_id']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def interactive_mode(master_agent: MasterAgent):
    """交互模式"""
    print("\n" + "=" * 60)
    print("🔮 六壬占卜系统 - 交互式命令行")
    print("=" * 60)
    print("\n使用说明:")
    print("  1. 输入占卜请求，例如: 8 6 男 明年爱情")
    print("  2. 输入 'q' 或 'quit' 退出")
    print("  3. 输入 'help' 查看示例\n")
    
    test_user_id = 1  # 使用测试用户ID
    
    while True:
        try:
            query = input("\n💬 请输入占卜请求: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['q', 'quit', 'exit']:
                print("\n👋 再见!")
                break
            
            if query.lower() == 'help':
                print("\n示例:")
                print("  8 6 男 明年爱情")
                print("  8, 6, 男, 想问一下我明年爱情怎么样")
                print("  3 7 女 事业发展")
                print("  5 2 男 财运如何")
                continue
            
            process_query(master_agent, test_user_id, query)
            
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")


def quick_test(master_agent: MasterAgent, query: str):
    """快速测试模式"""
    test_user_id = 1
    process_query(master_agent, test_user_id, query)


def main():
    """主函数"""
    # 创建数据库会话
    db_session = SessionLocal()
    
    try:
        # 初始化 MasterAgent
        master_agent = initialize_master_agent(db_session)
        
        # 检查命令行参数
        if len(sys.argv) > 1:
            # 快速测试模式
            query = " ".join(sys.argv[1:])
            quick_test(master_agent, query)
        else:
            # 交互模式
            interactive_mode(master_agent)
            
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
