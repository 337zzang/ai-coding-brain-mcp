"""
API 표준화를 위한 기본 클래스 및 인터페이스
모든 통합 모듈이 따라야 할 표준 패턴 정의
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic, Callable
from dataclasses import dataclass, field
from enum import Enum
import inspect

from .helper_result import HelperResult
from .error_handler import ErrorHandler, RetryPolicy, with_error_handling


T = TypeVar('T')


class OperationType(Enum):
    """작업 타입 분류"""
    READ = "read"           # 읽기 작업
    WRITE = "write"         # 쓰기 작업
    EXECUTE = "execute"     # 실행 작업
    SEARCH = "search"       # 검색 작업
    TRANSFORM = "transform" # 변환 작업


class ValidationLevel(Enum):
    """검증 레벨"""
    NONE = "none"         # 검증 없음
    BASIC = "basic"       # 기본 검증
    STRICT = "strict"     # 엄격한 검증
    FULL = "full"         # 전체 검증


@dataclass
class APIMetrics:
    """API 성능 메트릭"""
    call_count: int = 0
    total_time: float = 0.0
    error_count: int = 0
    last_called: Optional[float] = None
    average_time: float = 0.0
    
    def record_call(self, execution_time: float, success: bool = True):
        """호출 기록"""
        self.call_count += 1
        self.total_time += execution_time
        self.last_called = time.time()
        self.average_time = self.total_time / self.call_count
        
        if not success:
            self.error_count += 1


@dataclass
class ParameterSpec:
    """파라미터 명세"""
    name: str
    type_hint: type
    required: bool = True
    default: Any = None
    description: str = ""
    validator: Optional[Callable[[Any], bool]] = None


@dataclass
class APIOperation:
    """API 작업 정의"""
    name: str
    operation_type: OperationType
    parameters: List[ParameterSpec]
    description: str = ""
    examples: List[str] = field(default_factory=list)
    retry_policy: Optional[RetryPolicy] = None
    validation_level: ValidationLevel = ValidationLevel.BASIC


class ParameterValidator:
    """파라미터 검증 클래스"""
    
    @staticmethod
    def validate_required(params: Dict[str, Any], spec: ParameterSpec) -> bool:
        """필수 파라미터 검증"""
        if spec.required and spec.name not in params:
            raise ValueError(f"Required parameter '{spec.name}' is missing")
        return True
    
    @staticmethod
    def validate_type(value: Any, expected_type: type) -> bool:
        """타입 검증"""
        if value is not None and not isinstance(value, expected_type):
            # Union 타입 처리
            if hasattr(expected_type, '__origin__'):
                if expected_type.__origin__ is Union:
                    return any(isinstance(value, t) for t in expected_type.__args__)
            raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
        return True
    
    @staticmethod
    def validate_custom(value: Any, validator: Callable[[Any], bool]) -> bool:
        """커스텀 검증"""
        if validator and not validator(value):
            raise ValueError(f"Custom validation failed for value: {value}")
        return True
    
    @classmethod
    def validate_parameters(cls, params: Dict[str, Any], 
                          operation: APIOperation) -> Dict[str, Any]:
        """전체 파라미터 검증"""
        validated_params = {}
        
        for spec in operation.parameters:
            # 필수 파라미터 검증
            cls.validate_required(params, spec)
            
            value = params.get(spec.name, spec.default)
            
            if value is not None:
                # 타입 검증
                cls.validate_type(value, spec.type_hint)
                
                # 커스텀 검증
                if spec.validator:
                    cls.validate_custom(value, spec.validator)
            
            validated_params[spec.name] = value
        
        return validated_params


class ResponseFormatter:
    """응답 형식 표준화 클래스"""
    
    @staticmethod
    def format_success(data: Any, operation_name: str, 
                      execution_time: Optional[float] = None) -> HelperResult:
        """성공 응답 형식화"""
        result_data = {
            'result': data,
            'operation': operation_name,
            'timestamp': time.time()
        }
        
        if execution_time is not None:
            result_data['execution_time'] = execution_time
        
        return HelperResult(True, data=result_data)
    
    @staticmethod
    def format_error(error: Exception, operation_name: str, 
                    context: Optional[Dict[str, Any]] = None) -> HelperResult:
        """에러 응답 형식화"""
        error_data = {
            'operation': operation_name,
            'error_type': type(error).__name__,
            'timestamp': time.time()
        }
        
        if context:
            error_data['context'] = context
        
        return HelperResult(False, error=str(error), data=error_data)


class BaseAPI(ABC):
    """모든 API가 상속받아야 할 기본 클래스"""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"ai_helpers.{self.name.lower()}")
        self.error_handler = ErrorHandler()
        self.metrics: Dict[str, APIMetrics] = {}
        self.operations: Dict[str, APIOperation] = {}
        self._initialize_operations()
    
    @abstractmethod
    def _initialize_operations(self):
        """하위 클래스에서 지원하는 작업들을 정의"""
        pass
    
    def register_operation(self, operation: APIOperation):
        """작업 등록"""
        self.operations[operation.name] = operation
        self.metrics[operation.name] = APIMetrics()
    
    def _validate_operation(self, operation_name: str, 
                          params: Dict[str, Any]) -> Dict[str, Any]:
        """작업 검증"""
        if operation_name not in self.operations:
            raise ValueError(f"Unknown operation: {operation_name}")
        
        operation = self.operations[operation_name]
        return ParameterValidator.validate_parameters(params, operation)
    
    def _record_metrics(self, operation_name: str, execution_time: float, 
                       success: bool = True):
        """메트릭 기록"""
        if operation_name in self.metrics:
            self.metrics[operation_name].record_call(execution_time, success)
    
    def execute_operation(self, operation_name: str, **kwargs) -> HelperResult:
        """표준화된 작업 실행"""
        start_time = time.time()
        
        try:
            # 파라미터 검증
            validated_params = self._validate_operation(operation_name, kwargs)
            
            # 작업 실행
            operation = self.operations[operation_name]
            result = self._execute_core_operation(operation_name, validated_params)
            
            # 메트릭 기록
            execution_time = time.time() - start_time
            self._record_metrics(operation_name, execution_time, True)
            
            # 응답 형식화
            if isinstance(result, HelperResult):
                return result
            else:
                return ResponseFormatter.format_success(
                    result, operation_name, execution_time
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_metrics(operation_name, execution_time, False)
            
            self.logger.error(f"Operation {operation_name} failed: {e}")
            return ResponseFormatter.format_error(e, operation_name, kwargs)
    
    @abstractmethod
    def _execute_core_operation(self, operation_name: str, 
                              params: Dict[str, Any]) -> Any:
        """핵심 작업 실행 (하위 클래스에서 구현)"""
        pass
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """메트릭 조회"""
        return {
            name: {
                'call_count': metric.call_count,
                'total_time': metric.total_time,
                'average_time': metric.average_time,
                'error_count': metric.error_count,
                'error_rate': metric.error_count / max(metric.call_count, 1),
                'last_called': metric.last_called
            }
            for name, metric in self.metrics.items()
        }
    
    def reset_metrics(self):
        """메트릭 초기화"""
        for metric in self.metrics.values():
            metric.call_count = 0
            metric.total_time = 0.0
            metric.error_count = 0
            metric.last_called = None
            metric.average_time = 0.0
    
    def get_operations(self) -> Dict[str, Dict[str, Any]]:
        """지원 작업 목록 조회"""
        return {
            name: {
                'type': op.operation_type.value,
                'description': op.description,
                'parameters': [
                    {
                        'name': param.name,
                        'type': param.type_hint.__name__,
                        'required': param.required,
                        'description': param.description
                    }
                    for param in op.parameters
                ],
                'examples': op.examples
            }
            for name, op in self.operations.items()
        }
    
    def health_check(self) -> HelperResult:
        """헬스 체크"""
        try:
            status = {
                'api_name': self.name,
                'status': 'healthy',
                'operations_count': len(self.operations),
                'total_calls': sum(m.call_count for m in self.metrics.values()),
                'total_errors': sum(m.error_count for m in self.metrics.values()),
                'timestamp': time.time()
            }
            
            return HelperResult(True, data=status)
            
        except Exception as e:
            return HelperResult(False, error=f"Health check failed: {str(e)}")


class CachedAPI(BaseAPI):
    """캐시 기능이 있는 API 기본 클래스"""
    
    def __init__(self, name: str = None, cache_size: int = 1000):
        super().__init__(name)
        self.cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.max_cache_size = cache_size
    
    def _generate_cache_key(self, operation_name: str, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        import hashlib
        import json
        
        # 정렬된 파라미터로 일관된 키 생성
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        key_string = f"{operation_name}:{sorted_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _should_cache(self, operation_name: str) -> bool:
        """캐시 여부 결정 (읽기 작업만 캐시)"""
        operation = self.operations.get(operation_name)
        return operation and operation.operation_type == OperationType.READ
    
    def execute_operation(self, operation_name: str, **kwargs) -> HelperResult:
        """캐시를 고려한 작업 실행"""
        # 캐시 확인
        if self._should_cache(operation_name):
            cache_key = self._generate_cache_key(operation_name, kwargs)
            
            if cache_key in self.cache:
                self.cache_hits += 1
                self.logger.debug(f"Cache hit for {operation_name}")
                return self.cache[cache_key]
            else:
                self.cache_misses += 1
        
        # 실제 실행
        result = super().execute_operation(operation_name, **kwargs)
        
        # 성공한 읽기 작업 결과 캐시
        if (result.ok and self._should_cache(operation_name) and 
            len(self.cache) < self.max_cache_size):
            cache_key = self._generate_cache_key(operation_name, kwargs)
            self.cache[cache_key] = result
        
        return result
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / max(total_requests, 1)
        
        return {
            'cache_size': len(self.cache),
            'max_cache_size': self.max_cache_size,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate
        }