"""
解卦服务层
处理解卦和寻物分析的业务流程
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..xlr.adapters.liuren_adapter import LiurenAdapter
from ..xlr.schemas import PaipanResult, InterpretationResult, FindObjectResult
from backend.shared.db.models.divination import DivinationRecord, FindObjectRecord


class InterpretationService:
    """解卦服务类"""
    
    def __init__(self, liuren_adapter: LiurenAdapter, db_session: Optional[Session] = None):
        """
        初始化解卦服务
        
        Args:
            liuren_adapter: 小六壬算法适配器
            db_session: 数据库会话(可选，用于持久化)
        """
        self.liuren_adapter = liuren_adapter
        self.db_session = db_session
        
    def process_jiegua(
        self,
        paipan_result: PaipanResult,
        question_type: str,
        gender: str,
        user_id: Optional[int] = None,
        save_to_record: bool = True
    ) -> InterpretationResult:
        """
        处理解卦请求
        
        Args:
            paipan_result: 排盘结果
            question_type: 问题类型
            gender: 性别
            user_id: 用户ID(可选)
            save_to_record: 是否保存解卦结果到占卜记录
            
        Returns:
            解卦结果
        """
        # 调用算法适配器执行解卦
        inputs = {
            "operation": "jiegua",
            "paipan_result": paipan_result.model_dump(),
            "question_type": question_type,
            "gender": gender
        }
        
        result = self.liuren_adapter.run(inputs)
        
        # 转换为 InterpretationResult 对象
        interpretation_result = InterpretationResult(**result["interpretation_result"])
        
        # 如果需要，更新数据库中的占卜记录
        if save_to_record and user_id and self.db_session:
            self._update_record_interpretation(
                user_id=user_id,
                qigua_info=paipan_result.qigua_info,
                interpretation_data=interpretation_result.model_dump()
            )
            
        return interpretation_result
        
    def process_find_object(
        self,
        paipan_result: PaipanResult,
        item_description: str,
        user_id: Optional[int] = None,
        divination_record_id: Optional[int] = None,
        save_record: bool = True
    ) -> FindObjectResult:
        """
        处理寻物请求
        
        Args:
            paipan_result: 排盘结果
            item_description: 物品描述
            user_id: 用户ID(可选)
            divination_record_id: 关联的占卜记录ID(可选)
            save_record: 是否保存寻物记录
            
        Returns:
            寻物结果
        """
        # 验证物品描述长度
        if len(item_description) > 200:
            raise ValueError("物品描述长度不能超过200字符")
        
        # 调用算法适配器执行寻物分析
        inputs = {
            "operation": "find_object",
            "paipan_result": paipan_result.model_dump(),
            "item_description": item_description
        }
        
        result = self.liuren_adapter.run(inputs)
        
        # 转换为 FindObjectResult 对象
        find_object_result = FindObjectResult(**result["find_object_result"])
        
        # 保存寻物记录
        if save_record and user_id and self.db_session:
            self._save_find_object_record(
                user_id=user_id,
                divination_record_id=divination_record_id,
                item_description=item_description,
                find_object_result=find_object_result
            )
            
        return find_object_result
        
    def update_find_object_feedback(
        self,
        record_id: int,
        user_id: int,
        found_status: str,
        feedback: Optional[str] = None
    ) -> bool:
        """
        更新寻物记录的反馈信息
        
        Args:
            record_id: 寻物记录ID
            user_id: 用户ID(权限验证)
            found_status: 找到状态(found/not_found/unknown)
            feedback: 用户反馈
            
        Returns:
            是否更新成功
        """
        if not self.db_session:
            raise RuntimeError("需要数据库会话才能更新反馈")
        
        if found_status not in ["found", "not_found", "unknown"]:
            raise ValueError("found_status 必须是 found/not_found/unknown 之一")
        
        record = self.db_session.query(FindObjectRecord).filter(
            FindObjectRecord.id == record_id,
            FindObjectRecord.user_id == user_id
        ).first()
        
        if record:
            record.found_status = found_status
            if feedback:
                record.feedback = feedback
            self.db_session.commit()
            return True
        return False
        
    def get_find_object_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取寻物记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            寻物记录字典或None
        """
        if not self.db_session:
            raise RuntimeError("需要数据库会话才能查询记录")
        
        record = self.db_session.query(FindObjectRecord).filter(
            FindObjectRecord.id == record_id
        ).first()
        
        return self._find_object_record_to_dict(record) if record else None
        
    def get_user_find_object_history(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取用户的寻物历史
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            寻物历史字典
        """
        if not self.db_session:
            raise RuntimeError("需要数据库会话才能查询历史")
        
        query = self.db_session.query(FindObjectRecord).filter(
            FindObjectRecord.user_id == user_id
        )
        
        total_count = query.count()
        records = query.order_by(FindObjectRecord.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "records": [self._find_object_record_to_dict(record) for record in records],
            "total_count": total_count,
            "page": offset // limit + 1 if limit > 0 else 1,
            "page_size": limit
        }
        
    # ==================== 内部辅助方法 ====================
    
    def _update_record_interpretation(
        self,
        user_id: int,
        qigua_info: Any,
        interpretation_data: Dict[str, Any]
    ) -> None:
        """更新占卜记录的解卦数据"""
        if not self.db_session:
            return
        
        # 查找最近的匹配记录（基于起卦信息）
        # 这里简化处理，查找最近一条记录
        record = self.db_session.query(DivinationRecord).filter(
            DivinationRecord.user_id == user_id
        ).order_by(DivinationRecord.created_at.desc()).first()
        
        if record:
            record.interpretation_data = interpretation_data
            self.db_session.commit()
            
    def _save_find_object_record(
        self,
        user_id: int,
        divination_record_id: Optional[int],
        item_description: str,
        find_object_result: FindObjectResult
    ) -> None:
        """保存寻物记录到数据库"""
        if not self.db_session:
            return
        
        record = FindObjectRecord(
            user_id=user_id,
            divination_record_id=divination_record_id,
            item_description=item_description,
            direction_analysis=find_object_result.direction_analysis,
            location_clues=find_object_result.location_clues,
            time_estimation=find_object_result.time_estimation,
            success_probability=find_object_result.success_probability,
            detailed_guidance=find_object_result.detailed_guidance
        )
        
        self.db_session.add(record)
        self.db_session.commit()
        
    def _find_object_record_to_dict(self, record: FindObjectRecord) -> Dict[str, Any]:
        """将寻物记录转换为字典"""
        return {
            "id": record.id,
            "user_id": record.user_id,
            "divination_record_id": record.divination_record_id,
            "item_description": record.item_description,
            "direction_analysis": record.direction_analysis,
            "location_clues": record.location_clues,
            "time_estimation": record.time_estimation,
            "success_probability": record.success_probability,
            "detailed_guidance": record.detailed_guidance,
            "found_status": record.found_status,
            "feedback": record.feedback,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
