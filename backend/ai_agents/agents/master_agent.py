"""MasterAgent - 主控 Agent
协调 Orchestrator、Tools 和 Explainer 完成完整对话流程
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from .orchestrator import OrchestratorAgent
from .explainer import ExplainerAgent
from .registry import AlgorithmRegistry
from ..tools.rag_tool import RAGTool
from ..tools.profile_tool import ProfileTool
from ..tools.history_tool import HistoryTool
from ..services.divination_service import DivinationService
from ..services.rag_service import RAGService
from ..services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class MasterAgent:
    """主控 Agent - 协调所有子 Agent 和工具"""
    
    def __init__(
        self,
        orchestrator: OrchestratorAgent,
        explainer: ExplainerAgent,
        algorithm_registry: AlgorithmRegistry,
        divination_service: DivinationService,
        rag_service: RAGService,
        memory_service: MemoryService,
        tool_timeout: float = 10.0
    ):
        """
        初始化 MasterAgent
        
        Args:
            orchestrator: Orchestrator Agent 实例
            explainer: Explainer Agent 实例
            algorithm_registry: 算法注册表实例
            divination_service: 占卜服务实例
            rag_service: RAG 服务实例
            memory_service: 记忆服务实例
            tool_timeout: 工具调用超时时间（秒，默认 10 秒）
        """
        self.orchestrator = orchestrator
        self.explainer = explainer
        self.algorithm_registry = algorithm_registry
        self.divination_service = divination_service
        self.rag_service = rag_service
        self.memory_service = memory_service
        self.tool_timeout = tool_timeout
        
        # 初始化工具
        self.rag_tool = RAGTool(rag_service=rag_service)
        self.profile_tool = ProfileTool(memory_service=memory_service)
        self.history_tool = HistoryTool(divination_service=divination_service)
        
        # 线程池用于超时控制
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        logger.info("MasterAgent initialized with tool_timeout: %.1f seconds", tool_timeout)
    
    async def run(
        self,
        user_message: str,
        user_id: int,
        session_id: Optional[str] = None,
        conversation_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        执行完整对话流程
        
        Args:
            user_message: 用户消息
            user_id: 用户 ID
            session_id: 会话 ID（可选）
            conversation_history: 对话历史（可选）
            
        Returns:
            响应字典，包含 reply、divination_result、meta 等
        """
        logger.info(
            "MasterAgent run: user_id=%d, session_id=%s, message_len=%d",
            user_id, session_id, len(user_message)
        )
        
        start_time = datetime.now()
        
        try:
            # Step 1: Orchestrator 意图识别和槽位填充
            logger.info("Step 1: Calling Orchestrator")
            orchestrator_result = self.orchestrator.process(
                user_input=user_message,
                conversation_history=conversation_history or []
            )
            
            logger.debug("Orchestrator result: %s", orchestrator_result)
            
            # 检查是否需要追问
            if orchestrator_result.get("clarification_needed"):
                return {
                    "reply": orchestrator_result.get("clarification_message", "请提供更多信息"),
                    "status": "clarification_needed",
                    "missing_slots": orchestrator_result.get("missing_slots", []),
                    "meta": {
                        "processing_time": (datetime.now() - start_time).total_seconds()
                    }
                }
            
            # 检查是否就绪执行
            if not orchestrator_result.get("ready_to_execute"):
                error_msg = orchestrator_result.get("error_message", "无法理解您的问题")
                return {
                    "reply": error_msg,
                    "status": "error",
                    "meta": {
                        "processing_time": (datetime.now() - start_time).total_seconds()
                    }
                }
            
            # 提取槽位信息
            slots = orchestrator_result.get("slots", {})
            intent = orchestrator_result.get("intent", "divination")
            
            # Step 2: 调用工具执行占卜
            logger.info("Step 2: Calling tools with intent: %s", intent)
            divination_result = None
            
            if intent == "divination":
                divination_result = self._call_divination_tool(slots, user_id)
            else:
                return {
                    "reply": f"暂不支持 {intent} 意图",
                    "status": "unsupported_intent",
                    "meta": {
                        "processing_time": (datetime.now() - start_time).total_seconds()
                    }
                }
            
            if not divination_result or not divination_result.get("success"):
                error_msg = divination_result.get("error", "占卜失败") if divination_result else "占卜失败"
                return {
                    "reply": f"抱歉，{error_msg}。请稍后重试。",
                    "status": "tool_error",
                    "meta": {
                        "processing_time": (datetime.now() - start_time).total_seconds()
                    }
                }
            
            # Step 3 & 4: 并行获取 RAG 增强和用户画像
            logger.info("Step 3-4: Getting RAG enhancements and user profile in parallel")
            rag_chunks, user_profile = await asyncio.gather(
                self._call_rag_tool_async(slots, divination_result),
                self._call_profile_tool_async(user_id),
                return_exceptions=True  # 失败不影响整体流程
            )
            
            # 处理异常返回
            if isinstance(rag_chunks, Exception):
                logger.error("RAG tool failed with exception: %s", rag_chunks)
                rag_chunks = None
            if isinstance(user_profile, Exception):
                logger.error("Profile tool failed with exception: %s", user_profile)
                user_profile = None
            
            # Step 5: Explainer 生成解释
            logger.info("Step 5: Calling Explainer")
            explanation = self.explainer.generate_explanation(
                divination_result=divination_result.get("result", {}),
                question=user_message,
                question_type=slots.get("question_type", "综合"),
                rag_chunks=rag_chunks,
                user_profile=user_profile
            )
            
            # Step 6: 保存对话摘要（异步）
            logger.info("Step 6: Saving conversation summary")
            self._save_conversation_summary(
                user_id=user_id,
                session_id=session_id,
                user_message=user_message,
                agent_reply=explanation
            )
            
            # 返回完整响应
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info("MasterAgent completed in %.2f seconds", processing_time)
            
            return {
                "reply": explanation,
                "status": "success",
                "divination_result": divination_result.get("result", {}),
                "meta": {
                    "intent": intent,
                    "slots": slots,
                    "session_id": session_id,
                    "user_id": user_id,
                    "processing_time": processing_time,
                    "rag_used": len(rag_chunks) > 0 if rag_chunks else False,
                    "profile_used": user_profile is not None
                }
            }
            
        except Exception as e:
            logger.error("MasterAgent run failed: %s", e, exc_info=True)
            return {
                "reply": "抱歉，系统处理出错。请稍后重试。",
                "status": "error",
                "error": str(e),
                "meta": {
                    "processing_time": (datetime.now() - start_time).total_seconds()
                }
            }
    
    def _call_divination_tool(
        self,
        slots: Dict[str, Any],
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        通过算法注册表调用占卜算法（带超时保护）
        
        Args:
            slots: 槽位信息
            user_id: 用户 ID
            
        Returns:
            占卜结果或 None
        """
        try:
            # Step 1: 算法路由
            algorithm_hint = slots.get("algorithm_hint", "xlr-liuren")
            adapter = self.algorithm_registry.route(algorithm_hint)
            
            if not adapter:
                # 降级到默认算法
                adapter = self.algorithm_registry.get("xlr-liuren")
                if not adapter:
                    logger.error("No algorithm adapter available")
                    return {
                        "success": False,
                        "error": "算法不可用"
                    }
                logger.warning("Algorithm hint '%s' not found, using default xlr-liuren", algorithm_hint)
            
            logger.info("Using algorithm: %s", adapter.get_name())
            
            # Step 2: 准备算法输入（统一格式）
            algorithm_inputs = {
                "operation": "qigua",  # 或从 slots 获取
                "number1": int(slots.get("num1", 1)),
                "number2": int(slots.get("num2", 1)),
                "gender": slots.get("gender", "男"),
                "question_type": slots.get("question_type", "综合"),
                "qigua_time": slots.get("ask_time"),  # 如果有的话
            }
            
            # Step 3: 验证输入
            try:
                adapter.validate_input(algorithm_inputs)
            except ValueError as ve:
                logger.error("Algorithm input validation failed: %s", ve)
                return {
                    "success": False,
                    "error": f"输入参数错误：{ve}"
                }
            
            # Step 4: 执行算法（带超时）
            future = self.executor.submit(adapter.run, algorithm_inputs)
            algorithm_result = future.result(timeout=self.tool_timeout)
            
            # Step 5: 标准化输出
            return {
                "success": True,
                "result": algorithm_result,
                "algorithm_id": adapter.get_name()
            }
            
        except FuturesTimeoutError:
            logger.error("Algorithm execution timeout after %d seconds", self.tool_timeout)
            return {
                "success": False,
                "error": "算法执行超时"
            }
        except Exception as e:
            logger.error("Algorithm execution failed: %s", e, exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _call_rag_tool(
        self,
        slots: Dict[str, Any],
        divination_result: Dict[str, Any]
    ) -> Optional[list]:
        """
        调用 RAG 工具（带超时保护和降级）
        
        Args:
            slots: 槽位信息
            divination_result: 占卜结果
            
        Returns:
            RAG chunks 列表或 None
        """
        try:
            # 构建检索关键词
            keywords = []
            
            result_data = divination_result.get("result", {})
            qigua_data = result_data.get("qigua", {})
            jiegua_data = result_data.get("jiegua", {})
            
            if qigua_data.get("luogong_name"):
                keywords.append(qigua_data["luogong_name"])
            
            # yongshen 可能是列表或字符串
            yongshen = jiegua_data.get("yongshen")
            if yongshen:
                if isinstance(yongshen, list):
                    keywords.extend([str(y) for y in yongshen if y])
                else:
                    keywords.append(str(yongshen))
            
            if slots.get("question_type"):
                keywords.append(slots["question_type"])
            
            if not keywords:
                logger.info("No keywords for RAG search, skipping")
                return None
            
            # 调用 RAG（3 秒超时）
            rag_result = self.rag_tool.search(
                keywords=keywords,
                top_k=3,
                timeout=3.0
            )
            
            if rag_result.get("success"):
                return rag_result.get("chunks", [])
            else:
                logger.warning("RAG search failed or degraded")
                return None
                
        except Exception as e:
            logger.error("RAG tool failed: %s", e)
            return None
    
    def _call_profile_tool(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        调用用户画像工具（带降级）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户画像或 None
        """
        try:
            profile_result = self.profile_tool.get_profile(user_id)
            
            if profile_result.get("success"):
                return profile_result.get("profile")
            else:
                logger.warning("Profile tool failed")
                return None
                
        except Exception as e:
            logger.error("Profile tool failed: %s", e)
            return None
    
    async def _call_rag_tool_async(
        self,
        slots: Dict[str, Any],
        divination_result: Dict[str, Any]
    ) -> Optional[list]:
        """
        异步调用 RAG 工具（用于并行执行）
        
        Args:
            slots: 槽位信息
            divination_result: 占卜结果
            
        Returns:
            RAG chunks 列表或 None
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._call_rag_tool,
            slots,
            divination_result
        )
    
    async def _call_profile_tool_async(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        异步调用用户画像工具（用于并行执行）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户画像或 None
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._call_profile_tool,
            user_id
        )
    
    def _save_conversation_summary(
        self,
        user_id: int,
        session_id: Optional[str],
        user_message: str,
        agent_reply: str
    ):
        """
        保存对话摘要（非阻塞）
        
        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            user_message: 用户消息
            agent_reply: Agent 回复
        """
        try:
            # 这里应该调用 MemoryService 的方法保存对话
            # 但由于当前 MemoryService 可能没有相关方法，先记录日志
            logger.info(
                "TODO: Save conversation summary for user_id=%d, session_id=%s",
                user_id, session_id
            )
            # self.memory_service.update_conversation_summary(...)
            
        except Exception as e:
            logger.error("Failed to save conversation summary: %s", e)
            # 不影响主流程，静默失败
