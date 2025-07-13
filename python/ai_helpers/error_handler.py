"""
통합 에러 핸들링 시스템
자동 재시도, 에러 분류, 복구 메커니즘 제공
"""
import time
import logging
import traceback
from typing import Dict, Any, Optional, Callable, List, Union, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import inspect

T = TypeVar('T')


class ErrorCategory(Enum):
    """에러 카테고리 분류"""
    NETWORK = "network"           # 네트워크 관련 에러
    FILE_IO = "file_io"          # 파일 I/O 에러
    PERMISSION = "permission"     # 권한 관련 에러
    GIT = "git"                  # Git 관련 에러
    PARSE = "parse"              # 파싱 에러
    VALIDATION = "validation"     # 입력 검증 에러
    TIMEOUT = "timeout"          # 타임아웃 에러
    DEPENDENCY = "dependency"     # 의존성 에러
    UNKNOWN = "unknown"          # 알 수 없는 에러


class ErrorSeverity(Enum):
    """에러 심각도"""
    LOW = "low"           # 경고 수준
    MEDIUM = "medium"     # 일반 에러
    HIGH = "high"         # 심각한 에러
    CRITICAL = "critical" # 치명적 에러


@dataclass
class ErrorContext:
    """에러 컨텍스트 정보"""
    function_name: str
    parameters: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    stack_trace: str = field(default_factory=lambda: traceback.format_exc())
    attempt_count: int = 0
    previous_errors: List[str] = field(default_factory=list)


@dataclass
class RetryPolicy:
    """재시도 정책"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retry_on_categories: List[ErrorCategory] = field(default_factory=lambda: [
        ErrorCategory.NETWORK, ErrorCategory.TIMEOUT, ErrorCategory.FILE_IO
    ])
    
    def get_delay(self, attempt: int) -> float:
        """지수 백오프 지연 시간 계산"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class ErrorHandler:
    """통합 에러 핸들링 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger("ai_helpers.error_handler")
        self._error_patterns = self._initialize_error_patterns()
        self._recovery_strategies = self._initialize_recovery_strategies()
        self._error_stats = {
            "total_errors": 0,
            "by_category": {cat.value: 0 for cat in ErrorCategory},
            "by_severity": {sev.value: 0 for sev in ErrorSeverity},
            "recovery_success": 0,
            "retry_success": 0
        }
    
    def _initialize_error_patterns(self) -> Dict[ErrorCategory, List[str]]:
        """에러 패턴 매칭 규칙 초기화"""
        return {
            ErrorCategory.NETWORK: [
                "connection", "network", "dns", "resolve", "timeout", "unreachable"
            ],
            ErrorCategory.FILE_IO: [
                "no such file", "permission denied", "file not found", 
                "directory not found", "disk full", "read-only"
            ],
            ErrorCategory.PERMISSION: [
                "permission denied", "access denied", "forbidden", "unauthorized"
            ],
            ErrorCategory.GIT: [
                "not a git repository", "git", "remote", "branch", "merge conflict"
            ],
            ErrorCategory.PARSE: [
                "parse", "syntax", "invalid", "malformed", "decode"
            ],
            ErrorCategory.VALIDATION: [
                "validation", "invalid parameter", "missing required", "out of range"
            ],
            ErrorCategory.TIMEOUT: [
                "timeout", "timed out", "time limit", "deadline"
            ],
            ErrorCategory.DEPENDENCY: [
                "module not found", "import error", "missing dependency", "not installed"
            ]
        }
    
    def _initialize_recovery_strategies(self) -> Dict[ErrorCategory, Callable]:
        """에러별 복구 전략 초기화"""
        return {
            ErrorCategory.FILE_IO: self._recover_file_io,
            ErrorCategory.PERMISSION: self._recover_permission,
            ErrorCategory.GIT: self._recover_git,
            ErrorCategory.DEPENDENCY: self._recover_dependency,
        }
    
    def categorize_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """에러 분류 및 심각도 결정"""
        error_msg = str(error).lower()
        
        # 카테고리 결정
        category = ErrorCategory.UNKNOWN
        for cat, patterns in self._error_patterns.items():
            if any(pattern in error_msg for pattern in patterns):
                category = cat
                break
        
        # 심각도 결정
        severity = ErrorSeverity.MEDIUM
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            severity = ErrorSeverity.CRITICAL
        elif isinstance(error, (FileNotFoundError, ImportError)):
            severity = ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            severity = ErrorSeverity.MEDIUM
        elif "warning" in error_msg:
            severity = ErrorSeverity.LOW
            
        return category, severity
    
    def should_retry(self, error: Exception, category: ErrorCategory, 
                    retry_policy: RetryPolicy, attempt: int) -> bool:
        """재시도 여부 결정"""
        if attempt >= retry_policy.max_attempts:
            return False
            
        if category not in retry_policy.retry_on_categories:
            return False
            
        # 특정 에러는 재시도하지 않음
        if isinstance(error, (KeyboardInterrupt, SystemExit, SyntaxError)):
            return False
            
        return True
    
    def _recover_file_io(self, error: Exception, context: ErrorContext) -> bool:
        """파일 I/O 에러 복구 시도"""
        error_msg = str(error).lower()
        
        # 디렉토리 생성 시도
        if "no such file or directory" in error_msg:
            try:
                import os
                file_path = context.parameters.get('file_path') or context.parameters.get('path')
                if file_path:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    return True
            except Exception:
                pass
        
        return False
    
    def _recover_permission(self, error: Exception, context: ErrorContext) -> bool:
        """권한 에러 복구 시도"""
        # 실제 환경에서는 사용자에게 권한 요청 또는 대안 경로 제시
        self.logger.warning(f"Permission error in {context.function_name}. Manual intervention required.")
        return False
    
    def _recover_git(self, error: Exception, context: ErrorContext) -> bool:
        """Git 에러 복구 시도"""
        error_msg = str(error).lower()
        
        # Git 저장소 초기화 시도
        if "not a git repository" in error_msg:
            try:
                import subprocess
                subprocess.run(['git', 'init'], check=True, capture_output=True)
                return True
            except Exception:
                pass
        
        return False
    
    def _recover_dependency(self, error: Exception, context: ErrorContext) -> bool:
        """의존성 에러 복구 시도"""
        error_msg = str(error).lower()
        
        # 일반적인 모듈 설치 제안
        if "module not found" in error_msg or "import error" in error_msg:
            module_name = self._extract_module_name(str(error))
            if module_name:
                self.logger.warning(f"Missing module '{module_name}'. Please install with: pip install {module_name}")
        
        return False
    
    def _extract_module_name(self, error_msg: str) -> Optional[str]:
        """에러 메시지에서 모듈명 추출"""
        import re
        
        patterns = [
            r"No module named '([^']+)'",
            r"ModuleNotFoundError: No module named '([^']+)'",
            r"ImportError: No module named ([^\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                return match.group(1)
        
        return None
    
    def handle_error(self, error: Exception, context: ErrorContext, 
                    retry_policy: Optional[RetryPolicy] = None) -> tuple[bool, Optional[str]]:
        """에러 처리 메인 로직"""
        if retry_policy is None:
            retry_policy = RetryPolicy()
        
        category, severity = self.categorize_error(error)
        
        # 통계 업데이트
        self._error_stats["total_errors"] += 1
        self._error_stats["by_category"][category.value] += 1
        self._error_stats["by_severity"][severity.value] += 1
        
        # 로깅
        self.logger.error(
            f"Error in {context.function_name}: {error} "
            f"(Category: {category.value}, Severity: {severity.value})"
        )
        
        # 복구 시도
        recovery_strategy = self._recovery_strategies.get(category)
        if recovery_strategy:
            try:
                if recovery_strategy(error, context):
                    self._error_stats["recovery_success"] += 1
                    self.logger.info(f"Successfully recovered from {category.value} error")
                    return True, None
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}")
        
        # 재시도 결정
        should_retry = self.should_retry(error, category, retry_policy, context.attempt_count)
        
        if should_retry:
            delay = retry_policy.get_delay(context.attempt_count)
            self.logger.info(f"Retrying in {delay:.1f}s (attempt {context.attempt_count + 1})")
            return False, f"Retry in {delay:.1f}s"
        
        return False, f"{category.value} error: {str(error)}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """에러 처리 통계 반환"""
        return self._error_stats.copy()
    
    def reset_statistics(self):
        """통계 초기화"""
        self._error_stats = {
            "total_errors": 0,
            "by_category": {cat.value: 0 for cat in ErrorCategory},
            "by_severity": {sev.value: 0 for sev in ErrorSeverity},
            "recovery_success": 0,
            "retry_success": 0
        }


def with_error_handling(retry_policy: Optional[RetryPolicy] = None, 
                       auto_recovery: bool = True):
    """에러 핸들링 데코레이터"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            error_handler = ErrorHandler()
            
            # 함수 시그니처에서 파라미터 정보 추출
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            context = ErrorContext(
                function_name=func.__name__,
                parameters=dict(bound_args.arguments)
            )
            
            max_attempts = retry_policy.max_attempts if retry_policy else 3
            
            for attempt in range(max_attempts):
                context.attempt_count = attempt
                
                try:
                    result = func(*args, **kwargs)
                    
                    # 재시도 성공 통계 업데이트
                    if attempt > 0:
                        error_handler._error_stats["retry_success"] += 1
                    
                    return result
                    
                except Exception as e:
                    context.previous_errors.append(str(e))
                    
                    if not auto_recovery:
                        raise
                    
                    should_continue, message = error_handler.handle_error(e, context, retry_policy)
                    
                    if should_continue:
                        # 복구 성공, 다시 시도
                        continue
                    
                    if attempt == max_attempts - 1:
                        # 마지막 시도 실패
                        raise e
                    
                    # 재시도 대기
                    if retry_policy:
                        delay = retry_policy.get_delay(attempt)
                        time.sleep(delay)
            
            # 모든 시도 실패
            raise RuntimeError(f"All retry attempts failed for {func.__name__}")
        
        return wrapper
    return decorator


# 전역 에러 핸들러 인스턴스
_global_error_handler = ErrorHandler()


def get_error_statistics() -> Dict[str, Any]:
    """전역 에러 통계 반환"""
    return _global_error_handler.get_statistics()


def reset_error_statistics():
    """전역 에러 통계 초기화"""
    _global_error_handler.reset_statistics()