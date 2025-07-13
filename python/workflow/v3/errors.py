"""
워크플로우 v3 에러 정의 (간소화)
실제 사용되는 클래스만 포함
"""
from enum import Enum
from typing import Optional, Any, Dict


class ErrorCode(Enum):
    """에러 코드"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"
    TASK_ERROR = "TASK_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"


class WorkflowError(Exception):
    """워크플로우 에러"""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.WORKFLOW_ERROR, details: Any = None):
        super().__init__(message)
        self.code = code
        self.details = details


class ValidationError(WorkflowError):
    """검증 에러"""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, details)


class StorageError(WorkflowError):
    """저장소 에러"""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message, ErrorCode.STORAGE_ERROR, details)


class ExecutionError(WorkflowError):
    """실행 에러"""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message, ErrorCode.WORKFLOW_ERROR, details)


class InputValidator:
    """입력 검증 헬퍼"""

    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> None:
        """비어있지 않은 문자열 검증"""
        if not value or not value.strip():
            raise WorkflowError(
                f"{field_name} cannot be empty",
                ErrorCode.VALIDATION_ERROR
            )

    @staticmethod
    def validate_task_id(task_id: str) -> None:
        """태스크 ID 검증"""
        InputValidator.validate_non_empty_string(task_id, "Task ID")


# 기존 ErrorMessages 클래스는 제거 (사용 안함)


class ErrorMessages:
    """워크플로우 에러 메시지 모음"""

    # 일반 에러
    INVALID_COMMAND = "잘못된 명령어입니다"
    COMMAND_FAILED = "명령어 실행에 실패했습니다"
    INVALID_PARAMETER = "잘못된 매개변수입니다"

    # 플랜 관련 에러
    PLAN_NOT_FOUND = "플랜을 찾을 수 없습니다"
    PLAN_ALREADY_EXISTS = "이미 존재하는 플랜입니다"
    NO_ACTIVE_PLAN = "활성 플랜이 없습니다"
    PLAN_CREATE_FAILED = "플랜 생성에 실패했습니다"

    # 태스크 관련 에러
    TASK_NOT_FOUND = "태스크를 찾을 수 없습니다"
    TASK_ALREADY_EXISTS = "이미 존재하는 태스크입니다"
    NO_TASKS_AVAILABLE = "사용 가능한 태스크가 없습니다"
    TASK_CREATE_FAILED = "태스크 생성에 실패했습니다"

    # 상태 관련 에러
    INVALID_STATUS = "잘못된 상태입니다"
    STATUS_CHANGE_FAILED = "상태 변경에 실패했습니다"

    # 저장소 관련 에러
    STORAGE_READ_FAILED = "데이터 읽기에 실패했습니다"
    STORAGE_WRITE_FAILED = "데이터 저장에 실패했습니다"
    STORAGE_BACKUP_FAILED = "백업 생성에 실패했습니다"

    # 파일 관련 에러
    FILE_NOT_FOUND = "파일을 찾을 수 없습니다"
    FILE_READ_FAILED = "파일 읽기에 실패했습니다"
    FILE_WRITE_FAILED = "파일 쓰기에 실패했습니다"

    # 네트워크/Git 관련 에러
    GIT_COMMAND_FAILED = "Git 명령어 실행에 실패했습니다"
    NETWORK_ERROR = "네트워크 오류가 발생했습니다"

    @classmethod
    def get_message(cls, error_type, **kwargs):
        """에러 메시지 포맷팅"""
        message = getattr(cls, error_type, "알 수 없는 오류")

        # kwargs로 메시지 포맷팅
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError):
            return message

    @classmethod
    def format_error(cls, error_type, details=None, **kwargs):
        """에러 정보를 포맷팅하여 반환"""
        message = cls.get_message(error_type, **kwargs)

        if details:
            return f"{message}: {details}"
        else:
            return message


# 호환성을 위한 상수들
ERROR_INVALID_COMMAND = ErrorMessages.INVALID_COMMAND
ERROR_PLAN_NOT_FOUND = ErrorMessages.PLAN_NOT_FOUND
ERROR_TASK_NOT_FOUND = ErrorMessages.TASK_NOT_FOUND
ERROR_STORAGE_FAILED = ErrorMessages.STORAGE_READ_FAILED


class SuccessMessages:
    """워크플로우 성공 메시지 모음"""
    
    # 플랜 관련 성공 메시지
    PLAN_CREATED = "플랜 '{name}'이(가) 생성되었습니다"
    PLAN_ACTIVATED = "플랜 '{name}'이(가) 활성화되었습니다"
    PLAN_COMPLETED = "플랜 '{name}'이(가) 완료되었습니다"
    
    # 태스크 관련 성공 메시지
    TASK_CREATED = "태스크 '{title}'이(가) 생성되었습니다"
    TASK_COMPLETED = "태스크 '{title}'이(가) 완료되었습니다"
    TASK_UPDATED = "태스크 '{title}'이(가) 업데이트되었습니다"
    
    # 워크플로우 관련 성공 메시지
    WORKFLOW_STARTED = "워크플로우가 시작되었습니다"
    WORKFLOW_COMPLETED = "워크플로우가 완료되었습니다"
    
    @classmethod
    def get(cls, key: str, **kwargs) -> str:
        """성공 메시지 가져오기 및 포맷팅"""
        message = getattr(cls, key, "작업이 성공적으로 완료되었습니다")
        
        # kwargs로 메시지 포맷팅
        try:
            return message.format(**kwargs)
        except Exception:
            return message


class ErrorHandler:
    """워크플로우 에러 처리 핸들러"""

    def __init__(self):
        self.error_log = []
        self.max_log_size = 100

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """에러를 처리하고 표준화된 응답 반환"""
        error_info = {
            'timestamp': self._get_timestamp(),
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context or {}
        }

        # 에러 로그에 추가
        self.add_to_log(error_info)

        # 워크플로우 에러인 경우 상세 정보 포함
        if isinstance(error, WorkflowError):
            error_info.update({
                'error_category': error.error_type.value,
                'details': error.details
            })

        return self._create_error_response(error_info)

    def add_to_log(self, error_info: Dict[str, Any]):
        """에러 로그에 추가"""
        self.error_log.append(error_info)

        # 로그 크기 제한
        if len(self.error_log) > self.max_log_size:
            self.error_log.pop(0)

    def get_recent_errors(self, count: int = 10) -> list:
        """최근 에러들 반환"""
        return self.error_log[-count:] if self.error_log else []

    def clear_log(self):
        """에러 로그 초기화"""
        self.error_log.clear()

    def _get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _create_error_response(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            'success': False,
            'error': error_info['message'],
            'error_type': error_info['error_type'],
            'timestamp': error_info['timestamp'],
            'context': error_info.get('context', {}),
            'details': error_info.get('details', {})
        }

    @classmethod
    def create_validation_error(cls, message: str, field: str = None) -> ValidationError:
        """검증 에러 생성"""
        details = {'field': field} if field else {}
        return ValidationError(message, details)

    @classmethod 
    def create_storage_error(cls, message: str, operation: str = None) -> StorageError:
        """저장소 에러 생성"""
        details = {'operation': operation} if operation else {}
        return StorageError(message, details)

    @classmethod
    def create_execution_error(cls, message: str, command: str = None) -> ExecutionError:
        """실행 에러 생성"""
        details = {'command': command} if command else {}
        return ExecutionError(message, details)


# 전역 에러 핸들러 인스턴스
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """전역 에러 핸들러 반환"""
    return _error_handler


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """에러 처리 편의 함수"""
    return _error_handler.handle_error(error, context)


def log_error(message: str, error_type: str = 'general', context: Optional[Dict[str, Any]] = None):
    """에러 로깅 편의 함수"""
    error_info = {
        'timestamp': _error_handler._get_timestamp(),
        'error_type': error_type,
        'message': message,
        'context': context or {}
    }
    _error_handler.add_to_log(error_info)
