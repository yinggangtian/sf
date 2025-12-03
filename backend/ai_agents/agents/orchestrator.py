"""Orchestrator Agent
负责意图识别、槽位填充和算法路由
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from openai import OpenAI
from backend.shared.config.settings import get_settings

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """编排器 Agent - 负责意图识别和槽位填充"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Orchestrator Agent
        
        Args:
            api_key: OpenAI API 密钥（可选，默认从配置读取）
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = settings.openai_model_fast  # 使用快速模型做意图识别
        self.timeout = settings.openai_timeout
        # 关闭自动重试，避免累积等待时间
        self.client = OpenAI(
            api_key=self.api_key, 
            timeout=self.timeout,
            max_retries=0  # 关闭自动重试
        )
        
        # 加载 system prompt
        self.system_prompt = self._load_system_prompt()
        
        # 加载槽位填充模板
        self.slot_filling_templates = self._load_slot_filling_templates()
        
        # 最大追问次数
        self.max_follow_ups = 3
        
        logger.info("OrchestratorAgent initialized with model: %s", self.model)
    
    def _load_system_prompt(self) -> str:
        """从 YAML 文件加载 system prompt"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "system" / "orchestrator.yaml"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
                return prompt_data['content']
        except Exception as e:
            logger.error("Failed to load system prompt: %s", e)
            raise RuntimeError(f"无法加载 system prompt: {e}")
    
    def _load_slot_filling_templates(self) -> Dict[str, str]:
        """从 Markdown 文件加载槽位填充模板"""
        template_path = Path(__file__).parent.parent / "prompts" / "scenarios" / "slot_filling.md"
        
        templates = {}
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 简单解析 Markdown（按 ## 标题分段）
                sections = content.split('## ')
                for section in sections[1:]:  # 跳过第一个空段
                    lines = section.strip().split('\n', 1)
                    if len(lines) == 2:
                        title = lines[0].strip()
                        text = lines[1].strip().strip('>')
                        templates[title] = text.strip()
            
            logger.info("Loaded %d slot filling templates", len(templates))
            return templates
        except Exception as e:
            logger.error("Failed to load slot filling templates: %s", e)
            return {}
    
    def process(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        current_slots: Optional[Dict[str, Any]] = None,
        follow_up_count: int = 0,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理用户输入，进行意图识别和槽位填充（含输入 Guardrails）
        
        Args:
            user_input: 用户输入文本
            conversation_history: 对话历史（可选）
            current_slots: 当前已填充的槽位（可选）
            follow_up_count: 当前追问次数
            context_data: 上下文数据（可选，如地理位置、时间等）
            
        Returns:
            包含意图、槽位、追问信息的字典
        """
        logger.info("Processing user input with follow_up_count=%d", follow_up_count)
        
        # Step 0: 输入 Guardrails 验证
        validation_result = self._validate_input(user_input)
        if not validation_result["valid"]:
            return {
                "intent": "error",
                "ready_to_execute": False,
                "error_message": validation_result["error_message"],
                "slots": current_slots or {}
            }
        
        # 检查追问次数限制
        if follow_up_count >= self.max_follow_ups:
            return self._create_max_follow_ups_response()
        
        # 构建上下文提示
        context_prompt = self._build_context_prompt(current_slots, follow_up_count, context_data)
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": self.system_prompt + "\n\n" + context_prompt},
        ]
        
        # 添加对话历史
        if conversation_history:
            messages.extend(conversation_history)
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        try:
            # 调用 OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # 降低温度以提高稳定性
                response_format={"type": "json_object"}  # 强制 JSON 输出
            )
            
            result_text = response.choices[0].message.content
            logger.debug("LLM response: %s", result_text)
            
            # 解析 JSON 响应
            result = json.loads(result_text)
            
            # 验证和标准化结果
            normalized_result = self._normalize_result(result, follow_up_count, context_data)
            
            # 如果需要追问，生成追问消息
            if normalized_result.get("clarification_needed"):
                normalized_result["clarification_message"] = self._generate_clarification_message(
                    normalized_result.get("missing_slots", []),
                    normalized_result.get("slots", {})
                )
            
            logger.info("Intent: %s, Ready: %s, Missing: %s",
                       normalized_result.get("intent"),
                       normalized_result.get("ready_to_execute"),
                       normalized_result.get("missing_slots"))
            
            return normalized_result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            return self._create_error_response("解析失败，请重新描述您的问题")
        except Exception as e:
            logger.error("Error during LLM call: %s", e)
            return self._create_error_response("处理失败，请稍后重试")
    
    def _build_context_prompt(
        self, 
        current_slots: Optional[Dict[str, Any]], 
        follow_up_count: int,
        context_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建上下文提示"""
        context = ""
        
        if context_data:
            context += f"\n\n【环境上下文】\n"
            if context_data.get("local_time"):
                context += f"- 用户当地时间: {context_data['local_time']}\n"
            if context_data.get("location"):
                loc = context_data["location"]
                context += f"- 用户位置: {loc.get('country', '')} {loc.get('region', '')} {loc.get('city', '')}\n"
        
        if current_slots:
            context += f"\n\n当前已收集的槽位信息：\n{json.dumps(current_slots, ensure_ascii=False, indent=2)}"
        
        if follow_up_count > 0:
            context += f"\n\n当前追问次数：{follow_up_count}/{self.max_follow_ups}"
        
        return context
    
    def _normalize_result(
        self, 
        result: Dict[str, Any], 
        follow_up_count: int,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """标准化和验证 LLM 返回结果"""
        normalized = {
            "intent": result.get("intent", "divination"),
            "slots": result.get("slots", {}),
            "missing_slots": result.get("missing_slots", []),
            "clarification_needed": result.get("clarification_needed", False),
            "clarification_message": result.get("clarification_message", ""),
            "ready_to_execute": result.get("ready_to_execute", False),
            "follow_up_count": follow_up_count,
            "algorithm_hint": result.get("slots", {}).get("algorithm_hint", "xlr-liuren")
        }
        
        # 验证槽位值
        slots = normalized["slots"]
        validation_errors = []
        invalid_slots = []
        
        # 验证 num1 和 num2
        for num_field in ["num1", "num2"]:
            if num_field in slots and slots[num_field] is not None:
                try:
                    num_value = int(slots[num_field])
                    if num_value < 1:
                        validation_errors.append(f"{num_field}必须是正整数")
                        invalid_slots.append(num_field)
                        # 移除无效值
                        del slots[num_field]
                    else:
                        slots[num_field] = num_value
                except (ValueError, TypeError):
                    validation_errors.append(f"{num_field}必须是整数")
                    invalid_slots.append(num_field)
                    del slots[num_field]
        
        # 验证 gender
        if "gender" in slots and slots["gender"]:
            if slots["gender"] not in ["男", "女"]:
                validation_errors.append("性别必须是'男'或'女'")
                invalid_slots.append("gender")
                del slots["gender"]
        
        # 如果有验证错误，标记为需要追问
        if validation_errors:
            normalized["clarification_needed"] = True
            normalized["ready_to_execute"] = False
            normalized["validation_errors"] = validation_errors
            # 将无效的槽位添加到 missing_slots，前缀 invalid_
            normalized["missing_slots"].extend([f"invalid_{field}" for field in invalid_slots])
        
        # 检查必填槽位
        required_slots = ["num1", "num2", "gender"]
        missing = [s for s in required_slots if s not in slots or slots[s] is None]
        
        if missing:
            normalized["missing_slots"] = list(set(normalized["missing_slots"] + missing))
            normalized["clarification_needed"] = True
            normalized["ready_to_execute"] = False
        else:
            normalized["ready_to_execute"] = True
            normalized["clarification_needed"] = False
        
        # 设置默认值
        if "ask_time" not in slots or not slots["ask_time"]:
            # 优先使用上下文中的当地时间
            if context_data and context_data.get("local_time"):
                slots["ask_time"] = context_data["local_time"]
                print(f"qigua_time (from context) = {slots['ask_time']}")
            else:
                # 降级到系统当前时区时间
                slots["ask_time"] = datetime.now().astimezone().isoformat()
                print(f"qigua_time (system) = {slots['ask_time']}")
        
        if "question_type" not in slots or not slots["question_type"]:
            slots["question_type"] = "综合"
        
        return normalized
    
    def _generate_clarification_message(
        self,
        missing_slots: List[str],
        current_slots: Dict[str, Any]
    ) -> str:
        """生成追问消息"""
        # 检查是否有验证错误
        if any("invalid" in slot for slot in missing_slots):
            if "invalid_num1" in missing_slots or "invalid_num2" in missing_slots:
                return self.slot_filling_templates.get("报数范围错误", "报数必须在1到6之间")
            if "invalid_gender" in missing_slots:
                return self.slot_filling_templates.get("性别格式错误", "请提供有效的性别：男或女")
        
        # 过滤掉 invalid_ 前缀
        missing_slots = [s for s in missing_slots if not s.startswith("invalid_")]
        
        # 单个槽位缺失
        if len(missing_slots) == 1:
            slot = missing_slots[0]
            if slot in ["num1", "num2"]:
                return self.slot_filling_templates.get(
                    "缺失报数（num1 或 num2）",
                    "请问您想报哪两个数字？（1到6之间的整数）"
                )
            elif slot == "gender":
                return self.slot_filling_templates.get(
                    "缺失性别",
                    "请问您的性别是？（男/女）"
                )
            elif slot == "question_type":
                return self.slot_filling_templates.get(
                    "缺失问题类型",
                    "请问您想问什么方面的问题呢？"
                )
        
        # 多个槽位缺失
        slot_names = {
            "num1": "第一个报数",
            "num2": "第二个报数",
            "gender": "性别",
            "question_type": "问题类型"
        }
        
        missing_desc = "、".join([slot_names.get(s, s) for s in missing_slots])
        
        template = self.slot_filling_templates.get("多个槽位缺失", "")
        return template.replace("{missing_slots_description}", missing_desc)
    
    def _create_max_follow_ups_response(self) -> Dict[str, Any]:
        """创建达到最大追问次数的响应"""
        return {
            "intent": "error",
            "slots": {},
            "missing_slots": [],
            "clarification_needed": False,
            "clarification_message": self.slot_filling_templates.get(
                "追问次数超限",
                "看起来我们在沟通上有些困难。不如重新开始吧？"
            ),
            "ready_to_execute": False,
            "follow_up_count": self.max_follow_ups,
            "error": "max_follow_ups_exceeded"
        }
    
    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "intent": "error",
            "slots": {},
            "missing_slots": [],
            "clarification_needed": False,
            "clarification_message": message,
            "ready_to_execute": False,
            "follow_up_count": 0,
            "error": "processing_error"
        }
    
    def _validate_input(self, user_input: str) -> Dict[str, Any]:
        """
        输入 Guardrails：验证用户输入合法性
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            验证结果字典 {"valid": bool, "error_message": str}
        """
        # 1. 长度检查
        if not user_input or len(user_input.strip()) == 0:
            return {
                "valid": False,
                "error_message": "请输入您的问题"
            }
        
        if len(user_input) > 1000:
            return {
                "valid": False,
                "error_message": "问题过长，请精简到 1000 字以内"
            }
        
        # 2. 禁止特殊字符和 SQL 注入模式
        import re
        dangerous_patterns = [
            r"<script[^>]*>",  # XSS
            r"DROP\s+TABLE",   # SQL injection
            r"DELETE\s+FROM",
            r"INSERT\s+INTO",
            r"UPDATE\s+.*\s+SET"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning("Dangerous pattern detected in input: %s", pattern)
                return {
                    "valid": False,
                    "error_message": "输入包含非法字符，请使用自然语言提问"
                }
        
        # 3. 敏感词过滤
        forbidden_topics = [
            "政治", "暴力", "色情", "赌博", "毒品", "自杀", "犯罪",
            "生死", "疾病", "医疗", "股票", "彩票"
        ]
        
        for topic in forbidden_topics:
            if topic in user_input:
                logger.warning("Forbidden topic detected: %s", topic)
                return {
                    "valid": False,
                    "error_message": f"抱歉，本系统不支持关于「{topic}」的问题。占卜仅供娱乐参考，请勿用于重大决策。"
                }
        
        # 4. 数字范围预检查（如果包含数字）
        numbers = re.findall(r'\d+', user_input)
        for num_str in numbers:
            num = int(num_str)
            if num > 1000000:  # 异常大的数字
                return {
                    "valid": False,
                    "error_message": "输入包含异常数字，请检查后重试"
                }
        
        # 通过所有检查
        return {"valid": True, "error_message": ""}
