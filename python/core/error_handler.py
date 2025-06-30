"""
AI Coding Brain MCP - 표준 에러 처리 및 응답 형식
"""

from typing import Dict, Any, Optional, Union
from enum import Enum
import traceback
import logging

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """에러 타입 정의"""
    VALIDATION_ERROR = "validation_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    CONTEXT_ERROR = "context_error"
    PLAN_ERROR = "plan_error"
    TASK_ERROR = "task_error"
    SAVE_ERROR = "save_error"
    UNKNOWN_ERROR = "unknown_error"


class StandardResponse:
    """표준 응답 형식"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """성공 응답"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "error": None
        }
    
    @staticmethod
    def error(error_type: ErrorType, message: str, details: Optional[str] = None) -> Dict[str, Any]:
        """에러 응답"""
        response = {
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "type": error_type.value,
                "message": message
            }
        }
        
        if details:
            response["error"]["details"] = details
            
        return response


class ErrorHandler:
    """통합 에러 처리기"""
    
    @staticmethod
    def handle_exception(e: Exception, error_type: ErrorType = ErrorType.UNKNOWN_ERROR) -> Dict[str, Any]:
        """예외를 표준 에러 응답으로 변환"""
        error_message = str(e)
        error_details = traceback.format_exc()
        
        # 로깅
        logger.error(f"{error_type.value}: {error_message}")
        logger.debug(f"Traceback: {error_details}")
        
        # Wisdom 시스템에 오류 추적 (옵션)
        try:
            from project_wisdom import get_wisdom_manager
            wisdom = get_wisdom_manager()
            wisdom.track_error(error_type.value, error_message)
        except:
            pass  # Wisdom 시스템 접근 실패시 무시
        
        return StandardResponse.error(
            error_type=error_type,
            message=error_message,
            details=error_details if logger.level <= logging.DEBUG else None
        )
    
    @staticmethod
    def wrap_command(func):
        """명령어 함수를 표준 에러 처리로 감싸는 데코레이터"""
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # 함수가 이미 표준 응답을 반환하면 그대로 사용
                if isinstance(result, dict) and "success" in result:
                    return result
                # 아니면 성공 응답으로 감싸기
                return StandardResponse.success(data=result)
            except FileNotFoundError as e:
                return ErrorHandler.handle_exception(e, ErrorType.FILE_NOT_FOUND)
            except PermissionError as e:
                return ErrorHandler.handle_exception(e, ErrorType.PERMISSION_ERROR)
            except ValueError as e:
                return ErrorHandler.handle_exception(e, ErrorType.VALIDATION_ERROR)
            except Exception as e:
                return ErrorHandler.handle_exception(e, ErrorType.UNKNOWN_ERROR)
        
        return wrapper
