"""
워크플로우 v3 에러 정의 (간소화)
실제 사용되는 클래스만 포함
"""
from enum import Enum
from typing import Optional, Any


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
