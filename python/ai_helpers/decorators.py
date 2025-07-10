"""공통 데코레이터 모듈 - 향상된 버전"""
from .helper_result import HelperResult

import os
import functools
from typing import Callable, Any, Dict, Optional
from datetime import datetime
import json


def get_project_context():
    """ProjectContext 인스턴스를 가져오기"""
    try:
        from core.context_manager import get_context_manager
        manager = get_context_manager()
        if manager and manager.context:
            return manager.context
    except:
        pass
    return None


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
            # ProjectContext 가져오기
            context = get_project_context()
            
            # 디버그 모드 확인
            debug = os.environ.get('DEBUG_TRACKING', '').lower() == 'true'
            
            if debug:
                func_name = func.__name__
                print(f"🔍 {operation_type}:{action} - {func_name} 시작")
            
            start_time = datetime.now()
            
            try:
                # 실제 함수 실행
                result = func(*args, **kwargs)
                
                # 실행 시간 계산
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if debug:
                    print(f"✅ {operation_type}:{action} 성공 ({execution_time:.2f}초)")
                
                # 성공 추적
                _track_success(context, operation_type, action, args, kwargs, result, execution_time)
                
                # 특별 처리가 필요한 작업들
                if operation_type == 'file' and action in ['create', 'modify', 'read']:
                    _track_file_operation(context, action, args, kwargs)
                elif operation_type == 'code' and action in ['replace_block', 'insert_block']:
                    _track_code_operation(context, action, args, kwargs)
                
                # HelperResult로 래핑하여 반환
                from .helper_result import HelperResult
                # 이미 HelperResult인 경우 그대로 반환
                if isinstance(result, HelperResult):
                    return result
                return HelperResult(ok=True, data=result)
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if debug:
                    print(f"❌ {operation_type}:{action} 실패 ({execution_time:.2f}초): {e}")
                
                # 실패 추적
                _track_error(context, operation_type, action, e, args, kwargs, execution_time)
                
                # HelperResult로 에러 반환
                from .helper_result import HelperResult
                return HelperResult(ok=False, error=str(e))
        
        return wrapper
    return decorator


def _get_attr_safe(obj, attr, default=None):
    """객체나 dict에서 안전하게 속성/키 값을 가져오기"""
    if isinstance(obj, dict):
        return obj.get(attr, default)
    else:
        return getattr(obj, attr, default)


def _set_attr_safe(obj, attr, value):
    """객체나 dict에 안전하게 속성/키 값을 설정"""
    if isinstance(obj, dict):
        obj[attr] = value
    else:
        setattr(obj, attr, value)


def _track_success(context, operation_type: str, action: str, args: tuple, kwargs: dict, result: Any, execution_time: float):
    """작업 성공 추적 - 통합된 tracking 시스템 사용"""
    if not context:
        return
    
    # 통합 tracking 초기화
    if 'tracking' not in context:
        context['tracking'] = {
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
    
    tracking = context['tracking']
    
    # 전체 작업 로그에 추가
    operation_record = {
        'timestamp': datetime.now().isoformat(),
        'type': operation_type,
        'action': action,
        'execution_time': execution_time,
        'status': 'success',
        'function': args[0].__name__ if args and hasattr(args[0], '__name__') else None
    }
    
    tracking['operations'].append(operation_record)
    
    # 최근 1000개만 유지
    if len(tracking['operations']) > 1000:
        tracking['operations'] = tracking['operations'][-1000:]
    
    # 통계 업데이트
    tracking['statistics']['total_operations'] += 1
    tracking['statistics']['successful_operations'] += 1
    tracking['statistics']['total_execution_time'] += execution_time
    
    # 현재 태스크가 있으면 태스크별 추적
    current_task = _get_attr_safe(context, 'current_task')
    if current_task:
        if current_task not in tracking['tasks']:
            tracking['tasks'][current_task] = {
                'operations': [],
                'files_modified': set(),
                'files_accessed': set(),
                'functions_edited': set(),
                'start_time': datetime.now().isoformat(),
                'status': 'in_progress'
            }
        
        tracking['tasks'][current_task]['operations'].append(operation_record)


def _track_error(context, operation_type: str, action: str, error: Exception, args: tuple, kwargs: dict, execution_time: float):
    """작업 실패 추적 - 통합된 tracking 시스템 사용"""
    if not context:
        return
    
    # 통합 tracking 초기화
    if 'tracking' not in context:
        context['tracking'] = {
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
    
    tracking = context['tracking']
    
    # 에러 기록
    error_record = {
        'timestamp': datetime.now().isoformat(),
        'type': operation_type,
        'action': action,
        'error': str(error),
        'error_type': error.__class__.__name__,
        'execution_time': execution_time,
        'function': args[0].__name__ if args and hasattr(args[0], '__name__') else None
    }
    
    # 에러 로그에 추가
    tracking['errors'].append(error_record)
    
    # 최근 100개만 유지
    if len(tracking['errors']) > 100:
        tracking['errors'] = tracking['errors'][-100:]
    
    # 전체 작업 로그에도 추가
    operation_record = {**error_record, 'status': 'error'}
    tracking['operations'].append(operation_record)
    
    # 통계 업데이트
    tracking['statistics']['total_operations'] += 1
    tracking['statistics']['failed_operations'] += 1
    tracking['statistics']['total_execution_time'] += execution_time


def _track_file_operation(context, action: str, args: tuple, kwargs: dict):
    """파일 작업 추적 - 통합된 tracking 시스템 사용"""
    if not context or not args:
        return
        
    # 통합 tracking 초기화 확인
    if 'tracking' not in context:
        context['tracking'] = {
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
    
    tracking = context['tracking']
    
    # 파일 경로 추출
    file_path = args[0] if args else kwargs.get('path', kwargs.get('file_path', ''))
    
    # 파일별 추적
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
        'action': action,
        'task_id': _get_attr_safe(context, 'current_task')
    })
    
    # 최근 100개 작업만 유지
    if len(file_tracking['operations']) > 100:
        file_tracking['operations'] = file_tracking['operations'][-100:]
    
    # 현재 태스크의 파일 추적
    current_task = _get_attr_safe(context, 'current_task')
    if current_task and current_task in tracking['tasks']:
        task_tracking = tracking['tasks'][current_task]
        if action in ['create', 'modify', 'write']:
            task_tracking['files_modified'].add(file_path)
        else:
            task_tracking['files_accessed'].add(file_path)


def _track_code_operation(context, action: str, args: tuple, kwargs: dict):
    """코드 수정 작업 추적 - 통합된 tracking 시스템 사용"""
    if not context or len(args) < 2:
        return
        
    # 통합 tracking 초기화 확인
    if 'tracking' not in context:
        context['tracking'] = {
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
    
    tracking = context['tracking']
    
    file_path = args[0]
    block_name = args[1] if len(args) > 1 else kwargs.get('block_name', '')
    
    # 파일별 추적에 코드 수정 기록
    if file_path not in tracking['files']:
        tracking['files'][file_path] = {
            'first_accessed': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'access_count': 0,
            'operations': [],
            'code_edits': []  # 코드 수정 전용
        }
    
    file_tracking = tracking['files'][file_path]
    file_tracking['last_accessed'] = datetime.now().isoformat()
    
    # 코드 수정 기록
    edit_record = {
        'timestamp': datetime.now().isoformat(),
        'function': block_name,
        'action': action,
        'task_id': _get_attr_safe(context, 'current_task')
    }
    
    if 'code_edits' not in file_tracking:
        file_tracking['code_edits'] = []
    
    file_tracking['code_edits'].append(edit_record)
    
    # 최근 50개만 유지
    if len(file_tracking['code_edits']) > 50:
        file_tracking['code_edits'] = file_tracking['code_edits'][-50:]
    
    # 현재 태스크의 함수 편집 추적
    current_task = _get_attr_safe(context, 'current_task')
    if current_task and current_task in tracking['tasks']:
        task_tracking = tracking['tasks'][current_task]
        task_tracking['functions_edited'].add(f"{file_path}::{block_name}")
        if current_task in task_tracking:
            # functions_edited가 set인지 확인하고 아니면 set으로 변환
            if 'functions_edited' not in task_tracking[current_task]:
                task_tracking[current_task]['functions_edited'] = set()
            elif not isinstance(task_tracking[current_task]['functions_edited'], set):
                existing = task_tracking[current_task]['functions_edited']
                if isinstance(existing, str):
                    task_tracking[current_task]['functions_edited'] = {existing} if existing else set()
                elif isinstance(existing, list):
                    task_tracking[current_task]['functions_edited'] = set(existing)
                else:
                    task_tracking[current_task]['functions_edited'] = set()
            
            task_tracking[current_task]['functions_edited'].add(f'{file_path}::{block_name}')


def lazy_import(module_name: str, function_name: str):
    """지연 임포트 데코레이터
    
    Args:
        module_name: 임포트할 모듈 이름
        function_name: 임포트할 함수 이름
    
    Returns:
        지연 로딩을 수행하는 래퍼 함수
    """
    def lazy_wrapper(*args, **kwargs):
        import importlib
        import logging
        
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            return func(*args, **kwargs)
        except ImportError as e:
            # 친절한 경고 메시지
            print(f"⚠️ 모듈 '{module_name}'을 불러올 수 없어 {function_name} 기능이 비활성화됩니다.")
            print(f"   (이는 선택적 기능으로, 기본 동작에는 영향이 없습니다)")
            
            # 로그 파일에 상세 정보 기록
            logging.warning(f"[LazyImport] {function_name} 호출 실패: {e}")
            
            # 함수별 대체 동작
            if function_name in ['track_file_access', 'track_function_edit']:
                # ContextManager의 메서드로 대체 시도
                try:
                    from core.context_manager import get_context_manager
                    cm = get_context_manager()
                    if cm and hasattr(cm, function_name):
                        return getattr(cm, function_name)(*args, **kwargs)
                except:
                    pass
            
            # 기본 반환값
            return None
    
    lazy_wrapper.__name__ = function_name
    lazy_wrapper.__doc__ = f"Lazy-loaded from {module_name}.{function_name}"
    
    return lazy_wrapper
