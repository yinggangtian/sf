"""
占卜服务层
处理起卦、排盘的完整业务流程，协调算法引擎和数据持久化
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..xlr.adapters.liuren_adapter import LiurenAdapter
from ..xlr.schemas import QiguaRequest, PaipanResult
from backend.shared.db.models.divination import DivinationRecord
from .interpretation_service import InterpretationService


class DivinationService:
    """占卜服务类"""
    
    def __init__(
        self, 
        liuren_adapter: LiurenAdapter, 
        db_session: Session,
        interpretation_service: Optional[InterpretationService] = None
    ):
        """
        初始化占卜服务
        
        Args:
            liuren_adapter: 小六壬算法适配器
            db_session: 数据库会话（必需，用于持久化）
            interpretation_service: 解卦服务（可选，如未提供则创建新实例）
        """
        self.liuren_adapter = liuren_adapter
        self.db_session = db_session
        self.interpretation_service = interpretation_service or InterpretationService(
            liuren_adapter, db_session
        )
    
    def perform_divination(
        self,
        user_id: int,
        num1: int,
        num2: int,
        gender: str,
        ask_time: datetime,
        question_type: str,
        algorithm_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行完整占卜流程（槽位验证 → 起卦 → 解卦 → 生成解释 → 保存）
        
        Args:
            user_id: 用户ID
            num1: 第一个报数 (1-6)
            num2: 第二个报数 (1-6)
            gender: 性别（"男" 或 "女"）
            ask_time: 起卦时间
            question_type: 问题类型（如"事业"、"财运"、"感情"等）
            algorithm_hint: 算法提示（默认使用 xlr-liuren）
            
        Returns:
            包含 result, interpretation, meta 的字典
            
        Raises:
            ValueError: 槽位验证失败时抛出
        """
        # 1. 验证槽位完整性
        self._validate_slots(num1, num2, gender, ask_time, question_type)
        
        # 2. 验证算法提示（如果提供）
        if algorithm_hint and algorithm_hint != "xlr-liuren":
            raise ValueError(f"不支持的算法提示: {algorithm_hint}，当前仅支持 xlr-liuren")
        
        try:
            # 3. 执行起卦
            qigua_inputs = {
                "operation": "qigua",
                "number1": num1,
                "number2": num2,
                "qigua_time": ask_time,
                "question_type": question_type,
                "gender": gender
            }
            
            qigua_result = self.liuren_adapter.run(qigua_inputs)
            paipan_result = PaipanResult(**qigua_result["paipan_result"])
            
            # 4. 执行解卦
            jiegua_inputs = {
                "operation": "jiegua",
                "paipan_result": paipan_result.model_dump(),
                "question_type": question_type,
                "gender": gender
            }
            
            jiegua_result = self.liuren_adapter.run(jiegua_inputs)
            interpretation_data = jiegua_result["interpretation_result"]
            
            # 5. 生成人类可读解释（调用 InterpretationService）
            interpretation_text = self._generate_human_readable_interpretation(
                interpretation_data, question_type, gender
            )
            
            # 6. 保存结果到 DivinationHistory 表
            record = self._save_divination_record(
                user_id=user_id,
                qigua_data=paipan_result.qigua_info.model_dump(mode='json'),
                paipan_data=paipan_result.paipan_data,
                interpretation_data=interpretation_data,
                question_type=question_type,
                gender=gender
            )
            
            # 7. 返回统一格式
            return {
                "result": {
                    "paipan_result": paipan_result.model_dump(),
                    "interpretation_result": interpretation_data,
                    "record_id": record.id
                },
                "interpretation": interpretation_text,
                "meta": {
                    "algorithm": "xlr-liuren",
                    "user_id": user_id,
                    "question_type": question_type,
                    "gender": gender,
                    "ask_time": ask_time.isoformat(),
                    "created_at": record.created_at.isoformat() if record.created_at else None
                }
            }
            
        except Exception as e:
            self.db_session.rollback()
            raise RuntimeError(f"占卜流程执行失败: {str(e)}") from e
    
    def get_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        question_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        按 user_id 分页查询历史记录
        
        Args:
            user_id: 用户ID
            page: 页码（从1开始）
            page_size: 每页数量
            question_type: 问题类型筛选（可选）
            
        Returns:
            包含 items, total, page, page_size 的字典
        """
        if page < 1:
            raise ValueError("页码必须大于等于1")
        if page_size < 1 or page_size > 100:
            raise ValueError("每页数量必须在 1-100 之间")
        
        query = self.db_session.query(DivinationRecord).filter(
            DivinationRecord.user_id == user_id
        )
        
        if question_type:
            query = query.filter(DivinationRecord.question_type == question_type)
        
        total = query.count()
        offset = (page - 1) * page_size
        
        records = query.order_by(
            DivinationRecord.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        items = [self._record_to_dict(record) for record in records]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(records) < total
        }
    
    def get_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        统计用户占卜次数、常见问题类型
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        # 查询该用户所有记录
        records = self.db_session.query(DivinationRecord).filter(
            DivinationRecord.user_id == user_id
        ).all()
        
        if not records:
            return {
                "total_count": 0,
                "question_type_distribution": {},
                "most_common_type": None,
                "first_divination": None,
                "last_divination": None,
                "monthly_distribution": {}
            }
        
        # 统计问题类型分布
        question_types: Dict[str, int] = {}
        for record in records:
            q_type = record.question_type or "未分类"
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        # 找出最常见的问题类型
        most_common_type = max(question_types.items(), key=lambda x: x[1])[0] if question_types else None
        
        # 统计月度分布
        monthly_distribution: Dict[str, int] = {}
        for record in records:
            if record.created_at:
                month_key = record.created_at.strftime("%Y-%m")
                monthly_distribution[month_key] = monthly_distribution.get(month_key, 0) + 1
        
        # 排序记录以获取首次和最后占卜时间
        sorted_records = sorted(records, key=lambda r: r.created_at or datetime.min)
        
        return {
            "total_count": len(records),
            "question_type_distribution": question_types,
            "most_common_type": most_common_type,
            "first_divination": sorted_records[0].created_at.isoformat() if sorted_records[0].created_at else None,
            "last_divination": sorted_records[-1].created_at.isoformat() if sorted_records[-1].created_at else None,
            "monthly_distribution": monthly_distribution
        }
    
    # ==================== 内部辅助方法 ====================
    
    def _validate_slots(
        self,
        num1: int,
        num2: int,
        gender: str,
        ask_time: datetime,
        question_type: str
    ) -> None:
        """验证槽位完整性和合法性"""
        # 验证报数范围 (任意整数均可，算法会自动取模)
        # if not (1 <= num1 <= 6):
        #     raise ValueError("第一个报数必须在 1-6 之间")
        # if not (1 <= num2 <= 6):
        #     raise ValueError("第二个报数必须在 1-6 之间")
        
        # 验证性别
        if gender not in ["男", "女"]:
            raise ValueError("性别必须是 '男' 或 '女'")
        
        # 验证时间
        if ask_time > datetime.now():
            raise ValueError("起卦时间不能是未来时间")
        
        # 验证问题类型
        if not question_type or not question_type.strip():
            raise ValueError("问题类型不能为空")
    
    def _generate_human_readable_interpretation(
        self,
        interpretation_data: Dict[str, Any],
        question_type: str,
        gender: str
    ) -> str:
        """生成人类可读的解释文本"""
        yongshen = interpretation_data.get("yongshen", [])
        gong_analysis = interpretation_data.get("gong_analysis", {})
        comprehensive = interpretation_data.get("comprehensive_interpretation", "")
        
        # 构建解释文本
        parts = []
        parts.append(f"【问题类型】{question_type}")
        parts.append(f"【性别】{gender}")
        
        if yongshen:
            parts.append(f"【用神】{', '.join(yongshen)}")
        
        if gong_analysis:
            parts.append("\n【宫位分析】")
            for key, value in gong_analysis.items():
                if isinstance(value, dict):
                    parts.append(f"  {key}: {value.get('interpretation', value)}")
                else:
                    parts.append(f"  {key}: {value}")
        
        if comprehensive:
            parts.append(f"\n【综合解读】\n{comprehensive}")
        
        return "\n".join(parts)
    
    def _save_divination_record(
        self,
        user_id: int,
        qigua_data: Dict[str, Any],
        paipan_data: Dict[str, Any],
        interpretation_data: Dict[str, Any],
        question_type: str,
        gender: str
    ) -> DivinationRecord:
        """保存占卜记录到数据库"""
        record = DivinationRecord(
            user_id=user_id,
            qigua_data=qigua_data,
            paipan_data=paipan_data,
            interpretation_data=interpretation_data,
            question_type=question_type,
            gender=gender
        )
        
        self.db_session.add(record)
        self.db_session.commit()
        self.db_session.refresh(record)
        
        return record
    
    def _record_to_dict(self, record: DivinationRecord) -> Dict[str, Any]:
        """将 ORM 记录转换为字典"""
        return {
            "id": record.id,
            "user_id": record.user_id,
            "qigua_data": record.qigua_data,
            "paipan_data": record.paipan_data,
            "interpretation_data": record.interpretation_data,
            "question_type": record.question_type,
            "gender": record.gender,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
        
    def process_qigua(self, request: QiguaRequest, save_record: bool = True) -> PaipanResult:
        """
        处理起卦请求（完整业务流程）
        
        Args:
            request: 起卦请求
            save_record: 是否保存记录到数据库
            
        Returns:
            排盘结果
        """
        # 验证请求
        is_valid, error_msg = self.validate_qigua_request(request)
        if not is_valid:
            raise ValueError(f"起卦请求验证失败: {error_msg}")
        
        # 调用算法适配器执行起卦
        inputs = {
            "operation": "qigua",
            "number1": request.number1,
            "number2": request.number2,
            "qigua_time": request.qigua_time,
            "question_type": request.question_type,
            "gender": request.gender
        }
        
        result = self.liuren_adapter.run(inputs)
        
        # 转换为 PaipanResult 对象
        paipan_result = PaipanResult(**result["paipan_result"])
        
        # 保存记录（如果提供了用户ID和数据库会话）
        if save_record and request.user_id and self.db_session:
            self._save_divination_record(
                user_id=request.user_id,
                qigua_data=paipan_result.qigua_info.model_dump(mode='json'),
                paipan_data=paipan_result.paipan_data,
                interpretation_data={},  # 仅起卦时暂无解卦数据
                question_type=request.question_type or "",
                gender=request.gender or ""
            )
            
        return paipan_result
        
    def process_qigua_simple(
        self, 
        num1: int, 
        num2: int, 
        qigua_time: Optional[datetime] = None
    ) -> PaipanResult:
        """
        简化的起卦处理（不保存记录）
        
        Args:
            num1: 第一个报数(1-6)
            num2: 第二个报数(1-6)
            qigua_time: 起卦时间（可选，默认为当前时间）
            
        Returns:
            排盘结果
        """
        if qigua_time is None:
            qigua_time = datetime.now()
            
        request = QiguaRequest(
            number1=num1,
            number2=num2,
            qigua_time=qigua_time,
            question_type=None,
            gender=None, 
            user_id=None
        )
        
        return self.process_qigua(request, save_record=False)
    
    # ==================== 向后兼容的旧方法 ====================
        
    def get_user_divination_history(
        self, 
        user_id: int, 
        limit: int = 10, 
        offset: int = 0,
        question_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户的占卜历史
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            question_type: 问题类型筛选(可选)
            
        Returns:
            历史记录字典
        """
        if not self.db_session:
            raise RuntimeError("需要数据库会话才能查询历史记录")
        
        query = self.db_session.query(DivinationRecord).filter(
            DivinationRecord.user_id == user_id
        )
        
        if question_type:
            query = query.filter(DivinationRecord.question_type == question_type)
        
        total_count = query.count()
        records = query.order_by(DivinationRecord.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "records": [self._record_to_dict(record) for record in records],
            "total_count": total_count,
            "page": offset // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "has_more": offset + len(records) < total_count
        }
        
    def get_divination_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取特定的占卜记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            占卜记录字典或None
        """
        if not self.db_session:
            raise RuntimeError("需要数据库会话才能查询记录")
        
        record = self.db_session.query(DivinationRecord).filter(
            DivinationRecord.id == record_id
        ).first()
        
        return self._record_to_dict(record) if record else None
        
    def delete_divination_record(self, record_id: int, user_id: int) -> bool:
        """
        删除占卜记录
        
        Args:
            record_id: 记录ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            是否删除成功
        """
        if not self.db_session:
            raise RuntimeError("需要数据库会话才能删除记录")
        
        record = self.db_session.query(DivinationRecord).filter(
            DivinationRecord.id == record_id,
            DivinationRecord.user_id == user_id
        ).first()
        
        if record:
            self.db_session.delete(record)
            self.db_session.commit()
            return True
        return False
        
    def validate_qigua_request(self, request: QiguaRequest) -> tuple[bool, Optional[str]]:
        """
        验证起卦请求
        
        Args:
            request: 起卦请求
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查报数范围
        if not (1 <= request.number1 <= 6):
            return False, "第一个报数必须在1-6之间"
            
        if not (1 <= request.number2 <= 6):
            return False, "第二个报数必须在1-6之间"
            
        # 检查时间是否合理（不能太未来）
        if request.qigua_time > datetime.now():
            return False, "起卦时间不能是未来时间"
            
        return True, None
        
    def get_divination_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户占卜统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        if not self.db_session:
            raise RuntimeError("需要数据库会话才能查询统计")
        
        records = self.db_session.query(DivinationRecord).filter(
            DivinationRecord.user_id == user_id
        ).order_by(DivinationRecord.created_at.desc()).all()
        
        # 统计各种信息
        total_count = len(records)
        question_types: Dict[str, int] = {}
        monthly_counts: Dict[str, int] = {}
        
        for record in records:
            # 统计问题类型
            q_type = record.question_type or "未分类"
            question_types[q_type] = question_types.get(q_type, 0) + 1
            
            # 统计月度占卜次数
            month_key = record.created_at.strftime("%Y-%m")
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            
        return {
            "total_divinations": total_count,
            "question_type_distribution": question_types,
            "monthly_counts": monthly_counts,
            "last_divination": records[0].created_at.isoformat() if records else None,
            "average_per_month": round(total_count / max(len(monthly_counts), 1), 2)
        }
