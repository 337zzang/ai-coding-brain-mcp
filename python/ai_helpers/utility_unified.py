"""
통합 유틸리티 모듈 - Decorators, Utils, Legacy 기능 통합
핵심 데코레이터, 추적 시스템, 유틸리티 함수들을 하나로 정리
"""

import os
import functools
import importlib
import logging
from typing import Callable, Any, Dict, List, Optional, Set
from datetime import datetime
from .helper_result import HelperResult


class UnifiedTrackingSystem:
    """통합 추적 시스템 - 작업, 파일, 코드 수정 추적"""

    def __init__(self):
        self.debug_mode = os.environ.get('DEBUG_TRACKING', '').lower() == 'true'
        self._context_cache = {}

    def get_project_context(self) -> Optional[Dict[str, Any]]:
        """프로젝트 컨텍스트 가져오기 (여러 소스 시도)"""
        # 1. 통합 프로젝트 매니저에서 가져오기
        try:
            from .project_unified import _project_manager
            result = _project_manager.get_context()
            if result.ok:
                return result.data
        except:
            pass

        # 2. 기존 context_manager에서 가져오기
        try:
            from core.context_manager import get_context_manager
            manager = get_context_manager()
            if manager and manager.context:
                return manager.context
        except:
            pass

        # 3. 캐시된 컨텍스트 반환
        return self._context_cache.get('current_context')

    def track_operation_success(self, operation_type: str, action: str, 
                               args: tuple, kwargs: dict, result: Any, 
                               execution_time: float):
        """작업 성공 추적"""
        context = self.get_project_context()
        if not context:
            return

        # tracking 구조 초기화
        if 'tracking' not in context:
            context['tracking'] = self._init_tracking_structure()

        tracking = context['tracking']

        # 작업 기록
        operation_record = {
            'timestamp': datetime.now().isoformat(),
            'type': operation_type,
            'action': action,
            'execution_time': execution_time,
            'status': 'success'
        }

        tracking['operations'].append(operation_record)
        self._maintain_operation_limit(tracking['operations'], 1000)

        # 통계 업데이트
        stats = tracking['statistics']
        stats['total_operations'] += 1
        stats['successful_operations'] += 1
        stats['total_execution_time'] += execution_time

        if self.debug_mode:
            print(f"✅ {operation_type}:{action} 성공 ({execution_time:.2f}초)")

    def track_operation_error(self, operation_type: str, action: str, 
                             error: Exception, args: tuple, kwargs: dict, 
                             execution_time: float):
        """작업 실패 추적"""
        context = self.get_project_context()
        if not context:
            return

        if 'tracking' not in context:
            context['tracking'] = self._init_tracking_structure()

        tracking = context['tracking']

        # 에러 기록
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'type': operation_type,
            'action': action,
            'error': str(error),
            'error_type': error.__class__.__name__,
            'execution_time': execution_time,
            'status': 'error'
        }

        tracking['errors'].append(error_record)
        tracking['operations'].append(error_record)

        self._maintain_operation_limit(tracking['errors'], 100)
        self._maintain_operation_limit(tracking['operations'], 1000)

        # 통계 업데이트
        stats = tracking['statistics']
        stats['total_operations'] += 1
        stats['failed_operations'] += 1
        stats['total_execution_time'] += execution_time

        if self.debug_mode:
            print(f"❌ {operation_type}:{action} 실패 ({execution_time:.2f}초): {error}")

    def track_file_operation(self, file_path: str, action: str):
        """파일 작업 추적"""
        context = self.get_project_context()
        if not context:
            return

        if 'tracking' not in context:
            context['tracking'] = self._init_tracking_structure()

        tracking = context['tracking']

        # 파일별 추적 초기화
        if file_path not in tracking['files']:
            tracking['files'][file_path] = {
                'first_accessed': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'access_count': 0,
                'operations': []
            }

        file_tracking = tracking['files'][file_path]
        file_tracking['last_accessed'] = datetime.now().isoformat()
        file_tracking['access_count'] += 1
        file_tracking['operations'].append({
            'timestamp': datetime.now().isoformat(),
            'action': action
        })

        self._maintain_operation_limit(file_tracking['operations'], 100)

    def _init_tracking_structure(self) -> Dict[str, Any]:
        """추적 구조 초기화"""
        return {
            'tasks': {},
            'files': {},
            'operations': [],
            'errors': [],
            'statistics': {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'total_execution_time': 0
            }
        }

    def _maintain_operation_limit(self, operation_list: List, limit: int):
        """작업 목록 크기 제한 유지"""
        if len(operation_list) > limit:
            operation_list[:] = operation_list[-limit:]


# 전역 추적 시스템 인스턴스
_tracking_system = UnifiedTrackingSystem()


def track_operation(operation_type: str, action: str):
    """통합 작업 추적 데코레이터

    Args:
        operation_type: 작업 유형 ('git', 'build', 'context', 'file', 'code' 등)
        action: 구체적 동작 ('status', 'add', 'commit', 'create', 'modify' 등)

    Returns:
        데코레이터 함수
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()

            if _tracking_system.debug_mode:
                print(f"🔍 {operation_type}:{action} - {func.__name__} 시작")

            try:
                # 실제 함수 실행
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()

                # 성공 추적
                _tracking_system.track_operation_success(
                    operation_type, action, args, kwargs, result, execution_time
                )

                # 파일 작업 특별 처리
                if operation_type == 'file' and action in ['create', 'modify', 'read', 'write']:
                    file_path = args[0] if args else kwargs.get('path', kwargs.get('file_path', ''))
                    if file_path:
                        _tracking_system.track_file_operation(file_path, action)

                # HelperResult로 래핑
                if isinstance(result, HelperResult):
                    return result
                return HelperResult(ok=True, data=result)

            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()

                # 실패 추적
                _tracking_system.track_operation_error(
                    operation_type, action, e, args, kwargs, execution_time
                )

                return HelperResult(ok=False, error=str(e))

        return wrapper
    return decorator


def lazy_import(module_name: str, function_name: str):
    """지연 임포트 함수

    Args:
        module_name: 임포트할 모듈 이름
        function_name: 임포트할 함수 이름

    Returns:
        지연 로딩을 수행하는 래퍼 함수
    """
    def lazy_wrapper(*args, **kwargs):
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            return func(*args, **kwargs)
        except ImportError as e:
            print(f"⚠️ 모듈 '{module_name}'을 불러올 수 없어 {function_name} 기능이 비활성화됩니다.")
            logging.warning(f"[LazyImport] {function_name} 호출 실패: {e}")
            return None

    lazy_wrapper.__name__ = function_name
    lazy_wrapper.__doc__ = f"Lazy-loaded from {module_name}.{function_name}"
    return lazy_wrapper


def list_functions(module_or_instance) -> List[str]:
    """사용 가능한 함수 목록 표시

    Args:
        module_or_instance: 모듈 또는 클래스 인스턴스

    Returns:
        list: 사용 가능한 함수명 목록
    """
    funcs = [attr for attr in dir(module_or_instance)
             if not attr.startswith('_') and callable(getattr(module_or_instance, attr))]

    print(f"🔧 사용 가능한 함수 ({len(funcs)}개):")
    for func in sorted(funcs):
        print(f"  • {func}()")

    return funcs


def safe_import(module_path: str, function_name: Optional[str] = None):
    """안전한 임포트 with 에러 핸들링

    Args:
        module_path: 임포트할 모듈 경로
        function_name: 특정 함수명 (None이면 모듈 전체)

    Returns:
        임포트된 모듈 또는 함수, 실패 시 None
    """
    try:
        module = importlib.import_module(module_path)
        if function_name:
            return getattr(module, function_name, None)
        return module
    except ImportError as e:
        logging.warning(f"Safe import failed for {module_path}: {e}")
        return None


def get_tracking_statistics() -> HelperResult:
    """현재 추적 통계 정보 반환"""
    context = _tracking_system.get_project_context()
    if not context or 'tracking' not in context:
        return HelperResult(False, error="No tracking data available")

    stats = context['tracking']['statistics']
    return HelperResult(True, data=stats)


def reset_tracking() -> HelperResult:
    """추적 데이터 초기화"""
    context = _tracking_system.get_project_context()
    if context and 'tracking' in context:
        context['tracking'] = _tracking_system._init_tracking_structure()
        return HelperResult(True, data={'status': 'tracking_reset'})

    return HelperResult(False, error="No tracking context found")


# 하위 호환성을 위한 별칭들
track_file_access = _tracking_system.track_file_operation
get_project_context = _tracking_system.get_project_context
