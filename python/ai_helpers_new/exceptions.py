"""
Flow 시스템 예외 클래스
"""


class FlowError(Exception):
    """Flow 시스템 기본 예외"""
    pass


class ValidationError(FlowError):
    """검증 오류"""
    pass


class NotFoundError(FlowError):
    """리소스를 찾을 수 없음"""
    pass


class ConflictError(FlowError):
    """충돌 오류 (중복 등)"""
    pass


class PersistenceError(FlowError):
    """저장소 오류"""
    pass
