# exceptions.py
'''
Flow 시스템 예외 계층
o3 분석 결과를 기반으로 구현
'''

class FlowError(Exception):
    """Flow 시스템 기본 예외"""
    pass


class ValidationError(FlowError):
    """도메인 검증 실패"""
    pass


class SerializationError(FlowError):
    """직렬화/역직렬화 오류"""
    pass


class StorageError(FlowError):
    """파일 I/O 오류"""
    pass


class ConcurrencyError(FlowError):
    """동시성 제어 오류"""
    pass


class ContextError(FlowError):
    """Context 통합 오류"""
    pass
