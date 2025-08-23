"""
Error Messages Localization - 에러 메시지 한글화 및 상세화
생성일: 2025-08-23
"""

from typing import Dict, Any, Optional, Union
import traceback
import os

class ErrorMessages:
    """에러 메시지 한글화 및 상세화 클래스"""

    # 에러 코드별 메시지 매핑
    ERROR_CODES = {
        # 파일 시스템 에러
        "FILE_NOT_FOUND": {
            "ko": "파일을 찾을 수 없습니다: {path}",
            "en": "File not found: {path}",
            "hint": "파일 경로를 확인하거나 파일이 존재하는지 확인하세요."
        },
        "PERMISSION_DENIED": {
            "ko": "권한이 거부되었습니다: {path}",
            "en": "Permission denied: {path}",
            "hint": "파일 또는 디렉토리에 대한 읽기/쓰기 권한을 확인하세요."
        },
        "DIRECTORY_NOT_FOUND": {
            "ko": "디렉토리를 찾을 수 없습니다: {path}",
            "en": "Directory not found: {path}",
            "hint": "디렉토리 경로가 올바른지 확인하세요."
        },
        "FILE_EXISTS": {
            "ko": "파일이 이미 존재합니다: {path}",
            "en": "File already exists: {path}",
            "hint": "다른 파일명을 사용하거나 기존 파일을 삭제/이동하세요."
        },

        # Flow 시스템 에러
        "PLAN_NOT_FOUND": {
            "ko": "플랜을 찾을 수 없습니다: {plan_id}",
            "en": "Plan not found: {plan_id}",
            "hint": "플랜 ID를 확인하거나 flow_list_plans()로 목록을 확인하세요."
        },
        "TASK_NOT_FOUND": {
            "ko": "태스크를 찾을 수 없습니다: {task_id}",
            "en": "Task not found: {task_id}",
            "hint": "태스크 ID를 확인하거나 해당 플랜의 태스크 목록을 확인하세요."
        },
        "INVALID_STATUS": {
            "ko": "유효하지 않은 상태값: {status}",
            "en": "Invalid status: {status}",
            "hint": "가능한 상태: todo, in_progress, done, cancelled"
        },
        "PLAN_CREATE_FAILED": {
            "ko": "플랜 생성 실패: {reason}",
            "en": "Failed to create plan: {reason}",
            "hint": "플랜 이름이 중복되었거나 저장소 접근 권한을 확인하세요."
        },

        # Git 에러
        "GIT_NOT_INITIALIZED": {
            "ko": "Git 저장소가 초기화되지 않았습니다",
            "en": "Git repository not initialized",
            "hint": "git init 명령으로 저장소를 초기화하세요."
        },
        "GIT_COMMIT_FAILED": {
            "ko": "커밋 실패: {reason}",
            "en": "Commit failed: {reason}",
            "hint": "변경사항이 있는지 확인하고 git status로 상태를 확인하세요."
        },
        "GIT_BRANCH_EXISTS": {
            "ko": "브랜치가 이미 존재합니다: {branch}",
            "en": "Branch already exists: {branch}",
            "hint": "다른 브랜치명을 사용하거나 기존 브랜치를 삭제하세요."
        },

        # Python/코드 에러
        "SYNTAX_ERROR": {
            "ko": "구문 오류: {line}번 줄",
            "en": "Syntax error at line {line}",
            "hint": "코드 구문을 확인하세요. 괄호, 콜론, 들여쓰기 등을 점검하세요."
        },
        "IMPORT_ERROR": {
            "ko": "모듈을 가져올 수 없습니다: {module}",
            "en": "Cannot import module: {module}",
            "hint": "모듈이 설치되어 있는지 확인하거나 pip install로 설치하세요."
        },
        "TYPE_ERROR": {
            "ko": "타입 오류: {details}",
            "en": "Type error: {details}",
            "hint": "변수나 함수 인자의 타입을 확인하세요."
        },

        # 네트워크/API 에러
        "CONNECTION_ERROR": {
            "ko": "연결 오류: {url}",
            "en": "Connection error: {url}",
            "hint": "네트워크 연결을 확인하거나 URL이 올바른지 확인하세요."
        },
        "TIMEOUT_ERROR": {
            "ko": "시간 초과: {operation}",
            "en": "Timeout: {operation}",
            "hint": "작업이 너무 오래 걸립니다. 나중에 다시 시도하세요."
        },
        "API_ERROR": {
            "ko": "API 오류: {status_code} - {message}",
            "en": "API error: {status_code} - {message}",
            "hint": "API 문서를 확인하거나 요청 파라미터를 검토하세요."
        },

        # 일반 에러
        "UNKNOWN_ERROR": {
            "ko": "알 수 없는 오류가 발생했습니다",
            "en": "An unknown error occurred",
            "hint": "자세한 내용은 로그를 확인하세요."
        },
        "INVALID_ARGUMENT": {
            "ko": "잘못된 인자: {arg}",
            "en": "Invalid argument: {arg}",
            "hint": "함수 인자를 확인하세요."
        },
        "NOT_IMPLEMENTED": {
            "ko": "아직 구현되지 않은 기능입니다: {feature}",
            "en": "Not implemented yet: {feature}",
            "hint": "다른 방법을 사용하거나 기능 구현을 기다려주세요."
        }
    }

    @classmethod
    def get_message(cls, error_code: str, lang: str = "ko", **kwargs) -> Dict[str, str]:
        """에러 코드에 해당하는 메시지 반환

        Args:
            error_code: 에러 코드
            lang: 언어 (ko/en)
            **kwargs: 메시지 포맷팅 인자

        Returns:
            에러 메시지 딕셔너리
        """
        error_info = cls.ERROR_CODES.get(error_code, cls.ERROR_CODES["UNKNOWN_ERROR"])

        message = error_info.get(lang, error_info.get("en", "Unknown error"))
        hint = error_info.get("hint", "")

        # 메시지 포맷팅
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass  # 포맷팅 실패 시 원본 메시지 사용

        return {
            "code": error_code,
            "message": message,
            "hint": hint,
            "lang": lang
        }

    @classmethod
    def from_exception(cls, e: Exception, lang: str = "ko") -> Dict[str, str]:
        """예외 객체로부터 에러 메시지 생성

        Args:
            e: 예외 객체
            lang: 언어

        Returns:
            에러 메시지 딕셔너리
        """
        exception_type = type(e).__name__

        # 예외 타입별 에러 코드 매핑
        exception_mapping = {
            "FileNotFoundError": "FILE_NOT_FOUND",
            "PermissionError": "PERMISSION_DENIED",
            "IsADirectoryError": "DIRECTORY_NOT_FOUND",
            "FileExistsError": "FILE_EXISTS",
            "SyntaxError": "SYNTAX_ERROR",
            "ImportError": "IMPORT_ERROR",
            "ModuleNotFoundError": "IMPORT_ERROR",
            "TypeError": "TYPE_ERROR",
            "ConnectionError": "CONNECTION_ERROR",
            "TimeoutError": "TIMEOUT_ERROR",
            "NotImplementedError": "NOT_IMPLEMENTED"
        }

        error_code = exception_mapping.get(exception_type, "UNKNOWN_ERROR")

        # 에러 세부 정보 추출
        kwargs = {}
        if hasattr(e, 'filename'):
            kwargs['path'] = e.filename
        if hasattr(e, 'lineno'):
            kwargs['line'] = e.lineno
        if hasattr(e, 'name'):
            kwargs['module'] = e.name

        # 일반적인 에러 메시지에서 정보 추출
        error_str = str(e)
        if "'" in error_str:
            # 따옴표 안의 내용 추출 (파일명, 모듈명 등)
            import re
            matches = re.findall(r"'([^']*)'", error_str)
            if matches:
                if not kwargs.get('path'):
                    kwargs['path'] = matches[0]
                if not kwargs.get('module'):
                    kwargs['module'] = matches[0]

        kwargs['details'] = error_str
        kwargs['reason'] = error_str

        result = cls.get_message(error_code, lang, **kwargs)
        result['original_error'] = error_str
        result['exception_type'] = exception_type

        # 스택 트레이스 추가 (디버그 모드)
        if __debug__:
            result['stack_trace'] = traceback.format_exc()

        return result

    @classmethod
    def format_error_response(cls, error: Union[str, Exception, Dict],
                            lang: str = "ko") -> Dict[str, Any]:
        """에러를 표준 응답 형식으로 포맷팅

        Args:
            error: 에러 (문자열, 예외, 딕셔너리)
            lang: 언어

        Returns:
            표준 에러 응답
        """
        if isinstance(error, Exception):
            error_info = cls.from_exception(error, lang)
        elif isinstance(error, dict):
            error_info = error
        else:
            error_info = cls.get_message("UNKNOWN_ERROR", lang, details=str(error))

        return {
            "ok": False,
            "data": None,
            "error": error_info.get("message"),
            "error_detail": {
                "code": error_info.get("code"),
                "message": error_info.get("message"),
                "hint": error_info.get("hint"),
                "original": error_info.get("original_error"),
                "type": error_info.get("exception_type")
            }
        }


# 헬퍼 함수들
def localized_error(code: str, **kwargs):
    """한글화된 에러 메시지 생성"""
    return ErrorMessages.get_message(code, "ko", **kwargs)

def error_from_exception(e: Exception):
    """예외로부터 한글 에러 메시지 생성"""
    return ErrorMessages.from_exception(e, "ko")

def format_error(error: Union[str, Exception, Dict]):
    """에러를 표준 형식으로 포맷팅"""
    return ErrorMessages.format_error_response(error, "ko")


# Export
__all__ = [
    'ErrorMessages',
    'localized_error',
    'error_from_exception',
    'format_error'
]
