"""
API Decorators for Workflow V3
==============================

권한 체크, 로깅, 검증 등을 위한 데코레이터
"""

import functools
import logging
from typing import Callable, Any, Dict
from datetime import datetime
import traceback

from ..errors import WorkflowError, ErrorCode
from ..models import WorkflowEvent, EventType

logger = logging.getLogger(__name__)


def require_active_plan(func: Callable) -> Callable:
    """활성 플랜이 필요한 작업에 대한 데코레이터"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'state') or not self.state.current_plan:
            raise WorkflowError(
                ErrorCode.NO_ACTIVE_PLAN,
                "활성 플랜이 없습니다. 먼저 플랜을 생성하거나 선택하세요."
            )
        return func(self, *args, **kwargs)
    return wrapper


def log_command(command_type: str = "user"):
    """명령어 실행 로깅 데코레이터
    
    Args:
        command_type: "user" 또는 "internal"
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = datetime.now()
            command_name = func.__name__
            
            logger.info(f"[{command_type.upper()}] Executing {command_name}")
            
            try:
                result = func(self, *args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.info(
                    f"[{command_type.upper()}] {command_name} completed in {duration:.2f}s"
                )
                
                # 명령어 실행 이벤트 발행 (필요시)
                if hasattr(self, '_emit_command_event'):
                    self._emit_command_event(command_name, command_type, True, duration)
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"[{command_type.upper()}] {command_name} failed after {duration:.2f}s: {e}"
                )
                logger.debug(traceback.format_exc())
                
                # 실패 이벤트 발행
                if hasattr(self, '_emit_command_event'):
                    self._emit_command_event(command_name, command_type, False, duration, str(e))
                
                raise
                
        return wrapper
    return decorator


def validate_arguments(**validators):
    """인자 검증 데코레이터
    
    사용 예:
    @validate_arguments(title=lambda x: len(x) > 0, index=lambda x: x >= 0)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 함수 시그니처에서 인자 이름 추출
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()
            
            # 검증 실행
            for arg_name, validator in validators.items():
                if arg_name in bound.arguments:
                    value = bound.arguments[arg_name]
                    if not validator(value):
                        raise ValueError(f"Invalid {arg_name}: {value}")
                        
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def auto_save(func: Callable) -> Callable:
    """실행 후 자동 저장 데코레이터"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        
        # 저장 메서드가 있으면 실행
        if hasattr(self, '_save_data') and callable(self._save_data):
            try:
                self._save_data()
                logger.debug(f"Auto-saved after {func.__name__}")
            except Exception as e:
                logger.error(f"Auto-save failed: {e}")
                
        return result
    return wrapper


def transactional(func: Callable) -> Callable:
    """트랜잭션 데코레이터 - 실패 시 롤백"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # 상태 백업
        if hasattr(self, 'state'):
            import copy
            state_backup = copy.deepcopy(self.state)
            
        try:
            result = func(self, *args, **kwargs)
            return result
            
        except Exception as e:
            # 롤백
            if hasattr(self, 'state') and 'state_backup' in locals():
                self.state = state_backup
                logger.warning(f"Rolled back state after error in {func.__name__}")
            raise
            
    return wrapper


def rate_limit(max_calls: int = 10, window_seconds: int = 60):
    """Rate limiting 데코레이터"""
    call_times = []
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            now = datetime.now()
            
            # 오래된 호출 기록 제거
            nonlocal call_times
            call_times = [t for t in call_times 
                         if (now - t).total_seconds() < window_seconds]
            
            # Rate limit 체크
            if len(call_times) >= max_calls:
                raise WorkflowError(
                    ErrorCode.RATE_LIMIT_EXCEEDED,
                    f"Rate limit exceeded: {max_calls} calls per {window_seconds}s"
                )
            
            call_times.append(now)
            return func(self, *args, **kwargs)
            
        return wrapper
    return decorator


def internal_only(func: Callable) -> Callable:
    """내부 API 전용 데코레이터"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # 호출자 확인 (스택 분석)
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_module = caller_frame.f_globals.get('__name__', '')
        
        # 내부 모듈에서만 호출 허용
        if not caller_module.startswith('python.workflow'):
            logger.warning(
                f"Unauthorized call to internal API {func.__name__} from {caller_module}"
            )
            raise WorkflowError(
                ErrorCode.UNAUTHORIZED,
                "This is an internal API and cannot be called directly"
            )
            
        return func(self, *args, **kwargs)
    return wrapper


def deprecated(replacement: str = None):
    """Deprecated 경고 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            message = f"{func.__name__} is deprecated"
            if replacement:
                message += f". Use {replacement} instead"
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Export all decorators
__all__ = [
    'require_active_plan',
    'log_command',
    'validate_arguments',
    'auto_save',
    'transactional',
    'rate_limit',
    'internal_only',
    'deprecated'
]
