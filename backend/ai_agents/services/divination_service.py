"""
占卜服务层
处理起卦、排盘的完整业务流程，协调算法引擎和数据持久化
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..xlr.adapters.liuren_adapter import LiurenAdapter
from ..xlr.schemas import QiguaRequest, PaipanResult, QiguaInfo
from backend.shared.db.models.divination import DivinationRecord


class DivinationService:
    """占卜服务类"""
    
    def __init__(self, liuren_adapter: LiurenAdapter, db_session: Optional[Session] = None):
        """
        初始化占卜服务
        
        Args:
            liuren_adapter: 小六壬算法适配器
            db_session: 数据库会话(可选，用于持久化)
        """
        self.liuren_adapter = liuren_adapter
        self.db_session = db_session
        
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
                qigua_info=paipan_result.qigua_info,
                paipan_result=paipan_result,
                question_type=request.question_type,
                gender=request.gender
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
        
    # ==================== 内部辅助方法 ====================
    
    def _save_divination_record(
        self, 
        user_id: int, 
        qigua_info: QiguaInfo, 
        paipan_result: PaipanResult, 
        question_type: Optional[str],
        gender: Optional[str]
    ) -> None:
        """保存占卜记录到数据库"""
        if not self.db_session:
            return
        
        record = DivinationRecord(
            user_id=user_id,
            qigua_data=qigua_info.model_dump(),
            paipan_data=paipan_result.paipan_data,
            question_type=question_type,
            gender=gender
        )
        
        self.db_session.add(record)
        self.db_session.commit()
        
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
