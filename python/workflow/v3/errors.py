"""
Workflow v3 에러 처리 및 검증
통합된 에러 처리와 사용자 친화적 메시지
"""
from typing import Dict, Any, Optional, Type
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """에러 코드 정의"""
    # 입력 검증 에러
    EMPTY_TITLE = "empty_title"
    TITLE_TOO_LONG = "title_too_long"
    INVALID_COMMAND = "invalid_command"
    MISSING_ARGUMENT = "missing_argument"
    INVALID_ARGUMENT = "invalid_argument"
    
    # 상태 에러
    NO_ACTIVE_PLAN = "no_active_plan"
    NO_TASKS = "no_tasks"
    TASK_NOT_FOUND = "task_not_found"
    PLAN_NOT_FOUND = "plan_not_found"
    
    # 파일 시스템 에러
    FILE_NOT_FOUND = "file_not_found"
    FILE_CORRUPTED = "file_corrupted"
    SAVE_FAILED = "save_failed"
    LOAD_FAILED = "load_failed"
    
    # 권한 및 제한 에러
    PERMISSION_DENIED = "permission_denied"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # 일반 에러
    UNKNOWN_ERROR = "unknown_error"
    OPERATION_FAILED = "operation_failed"


class WorkflowError(Exception):
    """워크플로우 관련 커스텀 예외"""
    
    def __init__(self, code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
        
    def to_dict(self) -> Dict[str, Any]:
        """에러를 딕셔너리로 변환"""
        return {
            'error_code': self.code.value,
            'message': self.message,
            'details': self.details
        }


class ErrorMessages:
    """사용자 친화적 에러 메시지"""
    
    # 한국어 메시지 매핑
    MESSAGES = {
        ErrorCode.EMPTY_TITLE: "{field}을(를) 입력해주세요",
        ErrorCode.TITLE_TOO_LONG: "{field}은(는) {max_length}자를 초과할 수 없습니다",
        ErrorCode.INVALID_COMMAND: "알 수 없는 명령어입니다: {command}",
        ErrorCode.MISSING_ARGUMENT: "필수 인자가 누락되었습니다: {argument}",
        
        ErrorCode.NO_ACTIVE_PLAN: "활성 플랜이 없습니다. /plan으로 먼저 플랜을 생성하세요",
        ErrorCode.NO_TASKS: "태스크가 없습니다. /task로 태스크를 추가하세요",
        ErrorCode.TASK_NOT_FOUND: "태스크를 찾을 수 없습니다: {identifier}",
        ErrorCode.PLAN_NOT_FOUND: "플랜을 찾을 수 없습니다: {identifier}",
        
        ErrorCode.FILE_NOT_FOUND: "파일을 찾을 수 없습니다: {filename}",
        ErrorCode.FILE_CORRUPTED: "파일이 손상되었습니다. 백업에서 복원을 시도하세요",
        ErrorCode.SAVE_FAILED: "저장에 실패했습니다. 다시 시도해주세요",
        ErrorCode.LOAD_FAILED: "데이터 로드에 실패했습니다",
        
        ErrorCode.UNKNOWN_ERROR: "알 수 없는 오류가 발생했습니다",
        ErrorCode.OPERATION_FAILED: "작업을 수행할 수 없습니다: {reason}"
    }
    
    @classmethod
    def get(cls, code: ErrorCode, **kwargs) -> str:
        """에러 코드에 맞는 메시지 반환"""
        template = cls.MESSAGES.get(code, cls.MESSAGES[ErrorCode.UNKNOWN_ERROR])
        try:
            return template.format(**kwargs)
        except KeyError:
            return template



class InputValidator:
    """입력 검증 클래스"""
    
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 1000
    
    @classmethod
    def validate_title(cls, title: str, field_name: str = "제목") -> str:
        """제목 검증
        
        Args:
            title: 검증할 제목
            field_name: 필드 이름 (에러 메시지용)
            
        Returns:
            정규화된 제목
            
        Raises:
            WorkflowError: 검증 실패 시
        """
        if not title:
            raise WorkflowError(
                ErrorCode.EMPTY_TITLE,
                ErrorMessages.get(ErrorCode.EMPTY_TITLE, field=field_name)
            )
            
        title = title.strip()
        
        if not title:
            raise WorkflowError(
                ErrorCode.EMPTY_TITLE,
                ErrorMessages.get(ErrorCode.EMPTY_TITLE, field=field_name)
            )
            
        if len(title) > cls.MAX_TITLE_LENGTH:
            raise WorkflowError(
                ErrorCode.TITLE_TOO_LONG,
                ErrorMessages.get(ErrorCode.TITLE_TOO_LONG, 
                                field=field_name, 
                                max_length=cls.MAX_TITLE_LENGTH)
            )
            
        return title
        
    @classmethod
    def validate_description(cls, description: str) -> str:
        """설명 검증
        
        Args:
            description: 검증할 설명
            
        Returns:
            정규화된 설명
        """
        if not description:
            return ""
            
        description = description.strip()
        
        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            # 너무 긴 설명은 자르기
            description = description[:cls.MAX_DESCRIPTION_LENGTH] + "..."
            logger.warning("Description truncated due to length limit")
            
        return description
        
    @classmethod
    def validate_task_number(cls, number: str) -> int:
        """태스크 번호 검증
        
        Args:
            number: 검증할 번호 문자열
            
        Returns:
            정수 번호
            
        Raises:
            WorkflowError: 유효하지 않은 번호
        """
        try:
            num = int(number)
            if num < 1:
                raise ValueError("Task number must be positive")
            return num
        except ValueError:
            raise WorkflowError(
                ErrorCode.OPERATION_FAILED,
                ErrorMessages.get(ErrorCode.OPERATION_FAILED, 
                                reason="유효한 태스크 번호가 아닙니다")
            )



class ErrorHandler:
    """중앙 에러 처리기"""
    
    @staticmethod
    def handle_error(error: Exception, context: Optional[str] = None) -> Dict[str, Any]:
        """에러를 처리하고 사용자 친화적 응답 생성
        
        Args:
            error: 발생한 예외
            context: 에러 발생 컨텍스트
            
        Returns:
            에러 응답 딕셔너리
        """
        if isinstance(error, WorkflowError):
            # 커스텀 워크플로우 에러
            logger.error(f"Workflow error in {context}: {error.code} - {error.message}")
            return {
                'success': False,
                'error': error.message,
                'error_code': error.code.value,
                'details': error.details
            }
            
        elif isinstance(error, ValueError):
            # 일반적인 값 에러
            logger.error(f"Value error in {context}: {str(error)}")
            return {
                'success': False,
                'error': str(error),
                'error_code': ErrorCode.OPERATION_FAILED.value
            }
            
        elif isinstance(error, FileNotFoundError):
            # 파일 관련 에러
            logger.error(f"File not found in {context}: {str(error)}")
            return {
                'success': False,
                'error': ErrorMessages.get(ErrorCode.FILE_NOT_FOUND, 
                                         filename=str(error)),
                'error_code': ErrorCode.FILE_NOT_FOUND.value
            }
            
        else:
            # 예상치 못한 에러
            logger.exception(f"Unexpected error in {context}")
            return {
                'success': False,
                'error': ErrorMessages.get(ErrorCode.UNKNOWN_ERROR),
                'error_code': ErrorCode.UNKNOWN_ERROR.value,
                'details': {'original_error': str(error)}
            }
            
    @staticmethod
    def log_and_handle(func_name: str):
        """에러 로깅과 처리를 위한 데코레이터
        
        Args:
            func_name: 함수 이름 (로깅용)
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    return ErrorHandler.handle_error(e, func_name)
            return wrapper
        return decorator


def safe_execute(func, *args, default=None, **kwargs):
    """함수를 안전하게 실행하고 에러 시 기본값 반환
    
    Args:
        func: 실행할 함수
        *args: 함수 인자
        default: 에러 시 반환할 기본값
        **kwargs: 함수 키워드 인자
        
    Returns:
        함수 실행 결과 또는 기본값
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in safe_execute({func.__name__}): {e}")
        return default


# 사용자 친화적 성공 메시지
class SuccessMessages:
    """성공 메시지 템플릿"""
    
    PLAN_CREATED = "✅ 새 플랜 생성: {name}"
    PLAN_STARTED = "🚀 플랜 시작: {name}"
    PLAN_COMPLETED = "🎉 플랜 완료: {name}"
    PLAN_ARCHIVED = "📦 플랜 아카이브: {name}"
    
    TASK_ADDED = "✅ 태스크 추가: {title}"
    TASK_STARTED = "▶️ 태스크 시작: {title}"
    TASK_COMPLETED = "✅ 태스크 완료: {title}"
    TASK_UPDATED = "📝 태스크 업데이트: {title}"
    
    FILE_SAVED = "💾 파일 저장 완료"
    FILE_LOADED = "📂 파일 로드 완료"
    BACKUP_CREATED = "🔐 백업 생성 완료"
    
    @classmethod
    def get(cls, template_name: str, **kwargs) -> str:
        """성공 메시지 템플릿 반환"""
        template = getattr(cls, template_name, "작업 완료")
        try:
            return template.format(**kwargs)
        except:
            return template
