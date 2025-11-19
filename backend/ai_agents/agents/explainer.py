"""Explainer Agent
负责将结构化占卜结果转化为人类可读的解释
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from openai import OpenAI
from backend.shared.config.settings import get_settings

logger = logging.getLogger(__name__)


class ExplainerAgent:
    """解释生成器 Agent - 负责生成人类可读的占卜解释"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Explainer Agent
        
        Args:
            api_key: OpenAI API 密钥（可选，默认从配置读取）
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = settings.openai_model
        self.client = OpenAI(api_key=self.api_key)
        self.settings = settings
        
        # 加载 system prompt
        self.system_prompt = self._load_system_prompt()
        
        # 加载模板
        self.template = self._load_template()
        
        logger.info("ExplainerAgent initialized with model: %s", self.model)
    
    def _load_system_prompt(self) -> str:
        """从 YAML 文件加载 system prompt"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "system" / "explainer.yaml"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
                return prompt_data['content']
        except Exception as e:
            logger.error("Failed to load system prompt: %s", e)
            raise RuntimeError(f"无法加载 system prompt: {e}") from e
    
    def _load_template(self) -> str:
        """从 Markdown 文件加载模板"""
        template_path = Path(__file__).parent.parent / "prompts" / "templates" / "reply_basic.md"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error("Failed to load template: %s", e)
            raise RuntimeError(f"无法加载模板: {e}") from e
    
    def generate_explanation(
        self,
        divination_result: Dict[str, Any],
        question: str,
        question_type: str = "综合",
        rag_chunks: Optional[List[Dict[str, Any]]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        enable_judge: bool = True
    ) -> str:
        """
        生成占卜解释（支持 LLM-as-Judge 质量检查）
        
        Args:
            divination_result: 占卜结果（包含 paipan_result 和 interpretation_result）
            question: 用户问题
            question_type: 问题类型
            rag_chunks: RAG 检索到的知识片段（可选）
            user_profile: 用户画像（可选）
            enable_judge: 是否启用 LLM-as-Judge 评审（默认启用）
            
        Returns:
            生成的解释文本（已应用 Guardrails）
        """
        logger.info("Generating explanation for question_type: %s, judge_enabled: %s", 
                   question_type, enable_judge)
        
        # 组装 Prompt
        prompt = self._assemble_prompt(
            divination_result=divination_result,
            question=question,
            question_type=question_type,
            rag_chunks=rag_chunks,
            user_profile=user_profile
        )
        
        try:
            # Step 1: 生成初稿
            draft = self._generate_draft(prompt)
            
            if not draft:
                raise ValueError("LLM 返回空内容")
            
            logger.debug("Draft generated: %d chars", len(draft))
            
            # Step 2: LLM-as-Judge 评审（可选）
            if enable_judge:
                score = self._evaluate_draft(draft, question, divination_result)
                logger.info("Draft quality score: %.2f", score)
                
                # 低于 0.7 分需要重新生成
                if score < 0.7:
                    logger.warning("Draft quality below threshold (%.2f < 0.7), regenerating...", score)
                    draft = self._regenerate(prompt, draft, score)
            
            # Step 3: 应用输出 Guardrails
            safe_explanation = self._apply_guardrails(draft)
            
            # Step 4: 添加免责声明
            final_explanation = self._add_disclaimer(safe_explanation)
            
            logger.info("Explanation generated successfully: %d chars", len(final_explanation))
            
            return final_explanation
            
        except Exception as e:
            logger.error("Error generating explanation: %s", e)
            return self._generate_fallback_explanation(divination_result, question_type)
    
    def _generate_draft(self, prompt: str) -> str:
        """
        生成初稿
        
        Args:
            prompt: 组装好的 prompt
            
        Returns:
            初稿文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content or ""
    
    def _evaluate_draft(
        self,
        draft: str,
        question: str,
        divination_result: Dict[str, Any]
    ) -> float:
        """
        使用 LLM-as-Judge 评审初稿质量
        
        Args:
            draft: 初稿文本
            question: 用户问题
            divination_result: 占卜结果
            
        Returns:
            质量分数 (0.0-1.0)
        """
        evaluation_prompt = f"""你是一位专业的占卜解读质量评审员。请评估以下解读的质量。

**用户问题**：
{question}

**卦象结果**：
落宫：{divination_result.get('paipan_result', {}).get('luogong', '未知')}
用神：{divination_result.get('interpretation_result', {}).get('yongshen', '未知')}

**生成的解读**：
{draft}

**评审标准**：
1. **准确性** (0-3分)：解读是否符合卦象含义
2. **完整性** (0-3分)：是否覆盖用户问题的关键方面
3. **专业性** (0-2分)：措辞是否专业、谨慎，无绝对化断言
4. **可读性** (0-2分)：结构清晰、逻辑流畅

**输出格式**（仅输出 JSON）：
{{
  "accuracy_score": 0-3,
  "completeness_score": 0-3,
  "professionalism_score": 0-2,
  "readability_score": 0-2,
  "total_score": 0-10,
  "issues": ["问题1", "问题2"],
  "suggestions": ["改进建议1", "改进建议2"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是占卜解读质量评审专家。"},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.3,  # 降低随机性，提高稳定性
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content or "{}"
            
            # 提取 JSON（去除可能的 markdown 代码块标记）
            import json
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                total_score = result.get("total_score", 5)
                normalized_score = total_score / 10.0  # 归一化到 0-1
                
                logger.debug("Evaluation result: %s", result)
                return max(0.0, min(1.0, normalized_score))  # 限制在 [0, 1]
            else:
                logger.warning("Failed to parse evaluation result, using default 0.8")
                return 0.8
                
        except Exception as e:
            logger.error("Evaluation failed: %s", e)
            return 0.8  # 失败时给默认高分，避免阻塞
    
    def _regenerate(self, prompt: str, previous_draft: str, score: float) -> str:
        """
        根据评审结果重新生成解读
        
        Args:
            prompt: 原始 prompt
            previous_draft: 之前的初稿
            score: 评审分数
            
        Returns:
            改进后的解读
        """
        regenerate_prompt = f"""之前生成的解读质量评分为 {score:.2f}/1.0，未达到标准。请改进。

**原始要求**：
{prompt}

**之前的版本**（存在问题）：
{previous_draft}

**改进要求**：
1. 确保解读完整覆盖卦象含义
2. 避免绝对化断言（如"一定"、"必然"等）
3. 增强专业性和逻辑性
4. 保持结构清晰

请生成改进后的解读："""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": regenerate_prompt}
                ],
                temperature=0.6,  # 稍微降低创造性
                max_tokens=2000
            )
            
            improved = response.choices[0].message.content or previous_draft
            logger.info("Regenerated explanation: %d chars", len(improved))
            return improved
            
        except Exception as e:
            logger.error("Regeneration failed: %s, using original draft", e)
            return previous_draft  # 失败时返回原稿
    
    def _assemble_prompt(
        self,
        divination_result: Dict[str, Any],
        question: str,
        question_type: str,
        rag_chunks: Optional[List[Dict[str, Any]]],
        user_profile: Optional[Dict[str, Any]]
    ) -> str:
        """组装 Prompt（使用模板变量替换）"""
        # 提取排盘结果
        paipan_result = divination_result.get("paipan_result", {})
        interpretation_result = divination_result.get("interpretation_result", {})
        
        # 构建变量字典
        variables = {
            "question": question,
            "question_type": question_type,
            "ask_time": paipan_result.get("ask_time", "未知"),
            "gender": paipan_result.get("gender", "未知"),
            "num1": paipan_result.get("num1", "?"),
            "num2": paipan_result.get("num2", "?"),
            "luogong": paipan_result.get("luogong", "未知"),
            "luogong_wuxing": paipan_result.get("luogong_wuxing", ""),
            "shichen": paipan_result.get("shichen", "未知"),
            "shichen_dizhi": paipan_result.get("shichen_dizhi", ""),
            "yongshen": interpretation_result.get("yongshen", "未知"),
            "liugong_paipan": self._format_liugong_paipan(paipan_result.get("liugong_paipan", [])),
            "liushou_paipan": self._format_liushou_paipan(paipan_result.get("liushou_paipan", [])),
            "yongshen_analysis": interpretation_result.get("yongshen_analysis", ""),
            "gong_relations": self._format_gong_relations(interpretation_result.get("gong_relations", {})),
            "comprehensive_interpretation": interpretation_result.get("comprehensive_interpretation", ""),
            "rag_context": self._format_rag_context(rag_chunks) if rag_chunks else "无",
            "user_profile": self._format_user_profile(user_profile) if user_profile else "无"
        }
        
        # 替换模板变量
        prompt = self.template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    
    def _format_liugong_paipan(self, liugong_paipan: List[Dict]) -> str:
        """格式化六宫排盘"""
        if not liugong_paipan:
            return "无数据"
        
        lines = []
        for gong in liugong_paipan:
            position = gong.get("position", "?")
            name = gong.get("name", "?")
            wuxing = gong.get("wuxing", "?")
            lines.append(f"{position}. {name}（{wuxing}）")
        
        return "\n".join(lines)
    
    def _format_liushou_paipan(self, liushou_paipan: List[Dict]) -> str:
        """格式化六兽排盘"""
        if not liushou_paipan:
            return "无数据"
        
        lines = []
        for shou in liushou_paipan:
            position = shou.get("position", "?")
            name = shou.get("name", "?")
            lines.append(f"{position}. {name}")
        
        return "\n".join(lines)
    
    def _format_gong_relations(self, gong_relations: Dict) -> str:
        """格式化宫位关系"""
        if not gong_relations:
            return "无数据"
        
        lines = []
        for key, value in gong_relations.items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines) if lines else "无特殊关系"
    
    def _format_rag_context(self, rag_chunks: List[Dict[str, Any]]) -> str:
        """格式化 RAG 上下文"""
        if not rag_chunks:
            return "无"
        
        lines = []
        for i, chunk in enumerate(rag_chunks, 1):
            text = chunk.get("chunk_text", "")
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "未知来源")
            
            lines.append(f"{i}. 《{source}》：{text}")
        
        return "\n\n".join(lines)
    
    def _format_user_profile(self, user_profile: Dict[str, Any]) -> str:
        """格式化用户画像"""
        if not user_profile:
            return "无"
        
        lines = []
        
        if "gender" in user_profile:
            lines.append(f"- 性别：{user_profile['gender']}")
        
        if "total_divinations" in user_profile:
            lines.append(f"- 历史占卜次数：{user_profile['total_divinations']}")
        
        if "preferred_question_types" in user_profile:
            lines.append(f"- 常问问题：{user_profile['preferred_question_types']}")
        
        return "\n".join(lines) if lines else "无"
    
    def _apply_guardrails(self, text: str) -> str:
        """应用输出 Guardrails（过滤和替换禁用词、敏感内容）"""
        logger.debug("Applying guardrails to text: %d chars", len(text))
        
        modified_text = text
        replacements_made = []
        
        # 1. 获取 word_replacements（处理 Pydantic FieldInfo 类型）
        word_replacements = getattr(self.settings, 'word_replacements', {})
        if not isinstance(word_replacements, dict):
            word_replacements = {}
        
        # 2. 替换绝对化措辞
        absolute_words = {
            "一定": "很可能",
            "必然": "大概率",
            "绝对": "基本",
            "肯定": "应该",
            "永远": "长期",
            "完全": "大部分",
            "百分百": "很大程度上",
            "必须": "建议",
            "不会": "可能不会",
            "不可能": "不太可能"
        }
        absolute_words.update(word_replacements)  # 合并配置
        
        for forbidden_word, replacement in absolute_words.items():
            if forbidden_word in modified_text:
                modified_text = modified_text.replace(forbidden_word, replacement)
                replacements_made.append(f"{forbidden_word} -> {replacement}")
        
        # 3. 检查和过滤敏感内容
        sensitive_patterns = [
            (r'生死', '重要事务'),
            (r'死亡|丧命', '不利情况'),
            (r'疾病|癌症', '健康问题'),
            (r'暴力|伤害', '冲突'),
            (r'赌博|彩票', '投资'),
            (r'犯罪|违法', '不当行为')
        ]
        
        import re
        for pattern, replacement in sensitive_patterns:
            if re.search(pattern, modified_text):
                modified_text = re.sub(pattern, replacement, modified_text)
                replacements_made.append(f"{pattern} -> {replacement}")
                logger.warning("Sensitive content filtered: %s", pattern)
        
        # 4. 检查剩余的禁用词
        forbidden_absolute_words = getattr(self.settings, 'forbidden_absolute_words', [])
        remaining_forbidden = [
            word for word in forbidden_absolute_words
            if word in modified_text and word not in absolute_words
        ]
        
        # 5. 记录日志
        if replacements_made:
            logger.info("Guardrails replacements made: %d changes", len(replacements_made))
        
        if remaining_forbidden:
            logger.warning("Remaining forbidden words detected: %s", ", ".join(remaining_forbidden))
        
        return modified_text
    
    def _add_disclaimer(self, text: str) -> str:
        """添加免责声明"""
        disclaimer = f"\n\n---\n\n**温馨提示**：{self.settings.disclaimer_text}"
        return text + disclaimer
    
    def _generate_fallback_explanation(
        self,
        divination_result: Dict[str, Any],
        question_type: str
    ) -> str:
        """生成降级解释（当 LLM 调用失败时）"""
        logger.warning("Using fallback explanation")
        
        paipan_result = divination_result.get("paipan_result", {})
        interpretation_result = divination_result.get("interpretation_result", {})
        
        luogong = paipan_result.get("luogong", "未知")
        yongshen = interpretation_result.get("yongshen", "未知")
        
        fallback = f"""根据您的占卜结果，此卦落于{luogong}宫，用神为{yongshen}。

由于系统繁忙，我暂时无法生成详细解释。但从卦象来看，您所问的{question_type}问题有一定的积极迹象。

建议您稍后重试，或咨询专业的占卜师进行详细解读。

{self.settings.disclaimer_text}"""
        
        return fallback
