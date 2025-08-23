"""
API Response Standardization Module
API 응답 형식 표준화 모듈
생성일: 2025-08-23
"""

from typing import Any, Dict, Optional, List, Union
from datetime import datetime
import traceback

class APIResponse:
    """표준화된 API 응답 생성 클래스"""

    # 응답 타입 상수
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @staticmethod
    def success(
        data: Any = None,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """성공 응답 생성

        Args:
            data: 반환할 데이터
            message: 성공 메시지
            metadata: 추가 메타데이터

        Returns:
            표준화된 성공 응답
        """
        response = {
            "ok": True,
            "status": APIResponse.SUCCESS,
            "data": data,
            "message": message or "작업이 성공적으로 완료되었습니다.",
            "timestamp": datetime.now().isoformat(),
            "error": None
        }

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def error(
        error: Union[str, Exception],
        code: Optional[str] = None,
        data: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """에러 응답 생성

        Args:
            error: 에러 메시지 또는 예외 객체
            code: 에러 코드
            data: 부분적 데이터 (있는 경우)
            metadata: 추가 메타데이터

        Returns:
            표준화된 에러 응답
        """
        # 에러 메시지 추출
        if isinstance(error, Exception):
            error_msg = str(error)
            error_type = error.__class__.__name__
            # 디버그 모드에서는 스택 트레이스 포함
            stack_trace = traceback.format_exc() if __debug__ else None
        else:
            error_msg = str(error)
            error_type = "Error"
            stack_trace = None

        response = {
            "ok": False,
            "status": APIResponse.ERROR,
            "data": data,
            "message": f"오류가 발생했습니다: {error_msg}",
            "timestamp": datetime.now().isoformat(),
            "error": {
                "message": error_msg,
                "type": error_type,
                "code": code or "UNKNOWN_ERROR"
            }
        }

        if stack_trace:
            response["error"]["stack_trace"] = stack_trace

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def warning(
        message: str,
        data: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """경고 응답 생성

        Args:
            message: 경고 메시지
            data: 반환할 데이터
            metadata: 추가 메타데이터

        Returns:
            표준화된 경고 응답
        """
        response = {
            "ok": True,
            "status": APIResponse.WARNING,
            "data": data,
            "message": f"경고: {message}",
            "timestamp": datetime.now().isoformat(),
            "error": None,
            "warning": True
        }

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def info(
        message: str,
        data: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """정보 응답 생성

        Args:
            message: 정보 메시지
            data: 반환할 데이터
            metadata: 추가 메타데이터

        Returns:
            표준화된 정보 응답
        """
        response = {
            "ok": True,
            "status": APIResponse.INFO,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "error": None
        }

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def paginated(
        data: List[Any],
        page: int = 1,
        per_page: int = 10,
        total: Optional[int] = None,
        message: str = ""
    ) -> Dict[str, Any]:
        """페이지네이션 응답 생성

        Args:
            data: 데이터 목록
            page: 현재 페이지
            per_page: 페이지당 항목 수
            total: 전체 항목 수
            message: 메시지

        Returns:
            페이지네이션 정보가 포함된 응답
        """
        total = total or len(data)
        total_pages = (total + per_page - 1) // per_page

        return {
            "ok": True,
            "status": APIResponse.SUCCESS,
            "data": data,
            "message": message or f"페이지 {page}/{total_pages}",
            "timestamp": datetime.now().isoformat(),
            "error": None,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    @staticmethod
    def batch(
        results: List[Dict[str, Any]],
        message: str = ""
    ) -> Dict[str, Any]:
        """배치 작업 응답 생성

        Args:
            results: 개별 작업 결과 목록
            message: 메시지

        Returns:
            배치 작업 결과 응답
        """
        success_count = sum(1 for r in results if r.get("ok", False))
        error_count = len(results) - success_count

        return {
            "ok": error_count == 0,
            "status": APIResponse.SUCCESS if error_count == 0 else APIResponse.WARNING,
            "data": results,
            "message": message or f"성공: {success_count}개, 실패: {error_count}개",
            "timestamp": datetime.now().isoformat(),
            "error": None,
            "summary": {
                "total": len(results),
                "success": success_count,
                "error": error_count
            }
        }


# 기존 코드와의 호환성을 위한 헬퍼 함수
def ok(data=None, message=""):
    """성공 응답 (간단한 버전)"""
    return APIResponse.success(data, message)

def err(error, code=None):
    """에러 응답 (간단한 버전)"""
    return APIResponse.error(error, code)

def warn(message, data=None):
    """경고 응답 (간단한 버전)"""
    return APIResponse.warning(message, data)


# Response 검증 유틸리티
def is_success(response: Dict[str, Any]) -> bool:
    """응답이 성공인지 확인"""
    return response.get("ok", False) and response.get("status") != APIResponse.ERROR

def get_data(response: Dict[str, Any], default=None):
    """응답에서 데이터 안전하게 추출"""
    if is_success(response):
        return response.get("data", default)
    return default

def get_error(response: Dict[str, Any]) -> Optional[str]:
    """응답에서 에러 메시지 추출"""
    if not is_success(response):
        error_info = response.get("error", {})
        if isinstance(error_info, dict):
            return error_info.get("message", "Unknown error")
        return str(error_info) if error_info else "Unknown error"
    return None


# Export all
__all__ = [
    'APIResponse',
    'ok', 'err', 'warn',
    'is_success', 'get_data', 'get_error'
]
