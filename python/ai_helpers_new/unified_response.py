"""
Unified API Response System - 통합 API 응답 시스템
기존 util.py, wrappers.py, api_response.py 통합
생성일: 2025-08-23
"""

from typing import Any, Dict, Optional, List, Union
from datetime import datetime
import traceback
import pprint

class UnifiedResponse(dict):
    """
    통합 API 응답 클래스
    - dict 상속으로 완벽한 하위 호환성
    - REPL 최적화된 출력 (HelperResult 기능 통합)
    - 표준화된 응답 형식 (APIResponse 기능 통합)
    """

    def __init__(self, ok: bool = True, data: Any = None, 
                 error: Optional[str] = None, message: Optional[str] = None,
                 **kwargs):
        """통합 응답 객체 생성"""
        response = {
            'ok': ok,
            'data': data,
            'error': error,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        # 추가 필드 처리
        response.update(kwargs)
        super().__init__(response)

    # === 기존 util.py 호환성 메서드 ===
    @classmethod
    def ok(cls, data: Any = None, message: str = ""):
        """성공 응답 (util.py 호환)"""
        return cls(ok=True, data=data, message=message or "성공")

    @classmethod
    def err(cls, error: Union[str, Exception], code: Optional[str] = None):
        """에러 응답 (util.py 호환)"""
        if isinstance(error, Exception):
            error_msg = str(error)
            error_type = error.__class__.__name__
        else:
            error_msg = str(error)
            error_type = "Error"

        return cls(ok=False, error=error_msg, error_type=error_type, code=code)

    # === 기존 api_response.py 호환성 메서드 ===
    @classmethod
    def success(cls, data: Any = None, message: str = "", metadata: Optional[Dict] = None):
        """성공 응답 (api_response.py 호환)"""
        response = cls(ok=True, data=data, message=message or "작업 완료", 
                      status="success")
        if metadata:
            response['metadata'] = metadata
        return response

    @classmethod
    def warning(cls, message: str, data: Any = None):
        """경고 응답"""
        return cls(ok=True, data=data, message=f"⚠️ {message}", 
                  status="warning", warning=True)

    @classmethod
    def info(cls, message: str, data: Any = None):
        """정보 응답"""
        return cls(ok=True, data=data, message=message, status="info")

    # === HelperResult REPL 최적화 기능 ===
    def __repr__(self):
        """REPL에서의 표현"""
        return self._formatted_output()

    def __str__(self):
        """문자열 변환"""
        return self._formatted_output()

    def _formatted_output(self):
        """포맷팅된 출력 (HelperResult 스타일)"""
        if self.get('ok'):
            data = self.get('data')
            message = self.get('message', '')

            # 메시지가 있으면 함께 표시
            prefix = f"✅ {message}: " if message and message != "성공" else "✅ "

            if data is None:
                return f"{prefix}(완료)"

            # 데이터 타입별 출력
            try:
                if isinstance(data, list):
                    if len(data) == 0:
                        return f"{prefix}[] (빈 목록)"
                    elif len(data) <= 5:
                        formatted = pprint.pformat(data, indent=2, width=100)
                        return f"{prefix}\n{formatted}"
                    else:
                        preview = data[:3]
                        formatted = pprint.pformat(preview, indent=2, width=80)
                        return f"{prefix}[{len(data)}개 항목]\n{formatted}..."

                elif isinstance(data, dict):
                    if len(data) == 0:
                        return f"{prefix}{{}} (빈 딕셔너리)"
                    elif len(data) <= 5:
                        formatted = pprint.pformat(data, indent=2, width=100)
                        return f"{prefix}\n{formatted}"
                    else:
                        keys = list(data.keys())[:3]
                        preview = {k: data[k] for k in keys}
                        formatted = pprint.pformat(preview, indent=2, width=80)
                        return f"{prefix}[{len(data)}개 키]\n{formatted}..."

                elif isinstance(data, str):
                    if len(data) <= 200:
                        return f"{prefix}{repr(data)}"
                    else:
                        return f"{prefix}{repr(data[:200])}... ({len(data)}자)"

                elif isinstance(data, (int, float, bool)):
                    return f"{prefix}{data}"

                else:
                    return f"{prefix}{type(data).__name__}: {repr(data)}"

            except Exception as e:
                return f"{prefix}{repr(data)}"
        else:
            # 에러 출력
            error = self.get('error', '알 수 없는 오류')
            error_type = self.get('error_type', '')
            code = self.get('code', '')

            if error_type:
                prefix = f"❌ [{error_type}]"
            elif code:
                prefix = f"❌ [{code}]"
            else:
                prefix = "❌"

            return f"{prefix} {error}"

    # === 유틸리티 메서드 ===
    def is_ok(self) -> bool:
        """성공 여부 확인"""
        return self.get('ok', False)

    def get_data(self, default=None):
        """데이터 안전하게 추출"""
        if self.is_ok():
            return self.get('data', default)
        return default

    def get_error(self) -> Optional[str]:
        """에러 메시지 추출"""
        if not self.is_ok():
            return self.get('error', '알 수 없는 오류')
        return None


# === 헬퍼 함수 (하위 호환성) ===
def ok(data=None, message=""):
    """성공 응답 (간단한 버전)"""
    return UnifiedResponse.ok(data, message)

def err(error, code=None):
    """에러 응답 (간단한 버전)"""
    return UnifiedResponse.err(error, code)

def warn(message, data=None):
    """경고 응답"""
    return UnifiedResponse.warning(message, data)

def is_ok(result):
    """응답 성공 여부 확인"""
    if isinstance(result, UnifiedResponse):
        return result.is_ok()
    return result.get('ok', False) if isinstance(result, dict) else False

def get_data(result, default=None):
    """응답에서 데이터 추출"""
    if isinstance(result, UnifiedResponse):
        return result.get_data(default)
    if isinstance(result, dict) and result.get('ok'):
        return result.get('data', default)
    return default

def get_error(result):
    """응답에서 에러 추출"""
    if isinstance(result, UnifiedResponse):
        return result.get_error()
    if isinstance(result, dict) and not result.get('ok'):
        return result.get('error', '알 수 없는 오류')
    return None


# === 기존 함수 통합 ===
def safe_get_data(result, *fallback_keys):
    """KeyError 방지 안전한 데이터 추출 (util.py 호환)"""
    data = get_data(result)
    if data is not None:
        return data

    # Fallback 키 시도
    if isinstance(result, dict):
        for key in fallback_keys:
            if key in result:
                return result[key]

    return [] if not result else result

def normalize_api_response(result):
    """API 응답 정규화 (util.py 호환)"""
    if isinstance(result, UnifiedResponse):
        return result

    if isinstance(result, dict):
        if 'ok' in result:
            return UnifiedResponse(**result)

        # 에러 판단
        if 'error' in result or 'exception' in result:
            error = result.get('error') or result.get('exception', 'Unknown')
            return UnifiedResponse.err(error)

        # 데이터 추출
        if 'data' in result or 'items' in result:
            data = result.get('data') or result.get('items', result)
            return UnifiedResponse.ok(data)

    # 기본 처리
    return UnifiedResponse.ok(result)


# Export all
__all__ = [
    'UnifiedResponse',
    'ok', 'err', 'warn',
    'is_ok', 'get_data', 'get_error',
    'safe_get_data', 'normalize_api_response'
]
