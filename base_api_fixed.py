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

import helper_result
import error_handler

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
    retry_policy: Optional[error_handler.RetryPolicy] = None
    validation_level: ValidationLevel = ValidationLevel.BASIC

class BaseAPI(ABC):
    """모든 API가 상속받아야 할 기본 클래스"""

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"ai_helpers.{self.name.lower()}")
        self.error_handler = error_handler.ErrorHandler()
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

    def execute_operation(self, operation_name: str, **kwargs) -> helper_result.HelperResult:
        """표준화된 작업 실행"""
        start_time = time.time()

        try:
            # 작업 존재 확인
            if operation_name not in self.operations:
                raise ValueError(f"Unknown operation: {operation_name}")

            # 작업 실행
            result = self._execute_core_operation(operation_name, kwargs)

            # 메트릭 기록
            execution_time = time.time() - start_time
            self.metrics[operation_name].record_call(execution_time, True)

            # 응답 형식화
            if isinstance(result, helper_result.HelperResult):
                return result
            else:
                return helper_result.HelperResult(True, data={
                    'result': result,
                    'operation': operation_name,
                    'execution_time': execution_time,
                    'timestamp': time.time()
                })

        except Exception as e:
            execution_time = time.time() - start_time
            self.metrics[operation_name].record_call(execution_time, False)

            self.logger.error(f"Operation {operation_name} failed: {e}")
            return helper_result.HelperResult(False, error=str(e), data={
                'operation': operation_name,
                'error_type': type(e).__name__,
                'timestamp': time.time()
            })

    @abstractmethod
    def _execute_core_operation(self, operation_name: str, params: Dict[str, Any]) -> Any:
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

    def health_check(self) -> helper_result.HelperResult:
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

            return helper_result.HelperResult(True, data=status)

        except Exception as e:
            return helper_result.HelperResult(False, error=f"Health check failed: {str(e)}")
