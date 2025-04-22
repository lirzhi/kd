from datetime import datetime
from typing import Optional, List, Tuple
import logging
from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import SQLAlchemyError
from db import db_model as models
from db.dbutils.mysql_conn import MysqlConnection
from db.dbutils import singleton

logger = logging.getLogger(__name__)

@singleton
class RequireService:
    def __init__(self):
        # 使用线程安全的 scoped_session
        self.db_session = MysqlConnection().get_session()
      
    # region 装饰器统一处理事务和异常
    def _handle_db_operations(func):
        """统一处理数据库事务和异常的装饰器"""
        def wrapper(self, *args, **kwargs):
            try:
                result = func(self, *args,**kwargs)
                self.db_session.commit()
                return result
            except SQLAlchemyError as e:
                self.db_session.rollback()
                logger.error(f"Database operation failed: {str(e)}", exc_info=True)
                return OperationResult(False, error=str(e))
            except ValueError as e:
                logger.warning(f"Invalid parameters: {str(e)}")
                return OperationResult(False, error=str(e))
            finally:
                # scoped_session 会自动管理会话生命周期
                self.db_session.remove()
        return wrapper
    # endregion

    # region 核心CRUD操作
    @_handle_db_operations
    def create_requirement(
        self, 
        section_id: int, 
        parent_section: int, 
        requirement: str, 
        is_origin: bool = False
    ) -> 'OperationResult':
        """创建新的需求记录"""
        # 参数校验
        if not isinstance(section_id, int) or section_id <= 0:
            raise ValueError("section_id 必须为正整数")
        
        new_requirement = models.RequireInfo(
            section_id=section_id,
            parent_section=parent_section,
            requirement=requirement,
            is_origin=is_origin,
            create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.db_session.add(new_requirement)
        logger.info(f"创建需求: section_id={section_id}, parent={parent_section}")
        return OperationResult(True, data={"id": new_requirement.id})

    @_handle_db_operations
    def get_requirement_by_section(self, section_id) -> 'OperationResult':
        """根据章节ID获取需求"""
        print(section_id)
        requirements = self.db_session.query(models.RequireInfo).filter_by(section_id=section_id).all()
        print(section_id)
        return OperationResult(
            True, 
            data=[self._requirement_to_dict(r) for r in requirements]
        )

    @_handle_db_operations
    def delete_requirement_by_id(self, req_id: int) -> 'OperationResult':
        """根据ID删除需求"""
        if not isinstance(req_id, int) or req_id <= 0:
            raise ValueError("req_id 必须为正整数")
        
        deleted_count = self.db_session.query(models.RequireInfo)\
            .filter(models.RequireInfo.id == req_id)\
            .delete()
        logger.info(f"删除需求: id={req_id}, 影响行数={deleted_count}")
        return OperationResult(True, data={"deleted_rows": deleted_count})

    @_handle_db_operations
    def get_requirement_by_parent_section(
        self, 
        parent_section: int
    ) -> 'OperationResult':
        """根据父章节ID获取需求"""
        requirements = self.db_session.query(models.RequireInfo)\
            .filter(models.RequireInfo.parent_section == parent_section)\
            .all()
        return OperationResult(
            True, 
            data=[self._requirement_to_dict(r) for r in requirements]
        )
    # endregion

    # region 工具方法
    def _requirement_to_dict(self, requirement: models.RequireInfo) -> dict:
        """ORM对象转字典"""
        return {
            "id": requirement.id,
            "section_id": requirement.section_id,
            "parent_section": requirement.parent_section,
            "requirement": requirement.requirement,
            "is_origin": requirement.is_origin,
            "create_time": requirement.create_time.isoformat() 
                if requirement.create_time else None
        }
    # endregion

class OperationResult:
    """统一返回结果结构"""
    def __init__(
        self, 
        success: bool, 
        data: Optional[dict|list] = None, 
        error: Optional[str] = None
    ):
        self.success = success
        self.data = data
        self.error = error

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }