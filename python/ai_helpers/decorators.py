"""공통 데코레이터 모듈 - 향상된 버전"""
from helper_result import HelperResult

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
    """작업 성공 추적"""
    if not context:
        return
        
    # 현재 태스크 가져오기
    current_task = _get_attr_safe(context, 'current_task')
    if not current_task:
        return
    
    # metadata 가져오기
    metadata = _get_attr_safe(context, 'metadata', {})
    if not isinstance(metadata, dict):
        metadata = {}
    
    # task_tracking이 metadata에 있는지 확인
    if 'task_tracking' not in metadata:
        metadata['task_tracking'] = {}
    
    task_tracking = metadata['task_tracking']
    
    # 현재 태스크의 추적 정보가 없으면 생성
    if current_task not in task_tracking:
        task_tracking[current_task] = {
            'operations': [],
            'files_modified': set(),
            'files_accessed': set(),
            'functions_edited': set(),
            'start_time': datetime.now().isoformat(),
            'status': 'in_progress'
        }
    
    # 작업 기록 추가
    operation_record = {
        'timestamp': datetime.now().isoformat(),
        'type': operation_type,
        'action': action,
        'execution_time': execution_time,
        'function': args[0].__name__ if args and hasattr(args[0], '__name__') else None
    }
    
    task_tracking[current_task]['operations'].append(operation_record)
    
    # metadata 다시 설정
    _set_attr_safe(context, 'metadata', metadata)


def _track_error(context, operation_type: str, action: str, error: Exception, args: tuple, kwargs: dict, execution_time: float):
    """작업 실패 추적"""
    if not context:
        return
    
    # 오류 로그에 추가
    error_record = {
        'timestamp': datetime.now().isoformat(),
        'type': operation_type,
        'action': action,
        'error': str(error),
        'error_type': error.__class__.__name__,
        'execution_time': execution_time
    }
    
    # error_log 가져오기/설정
    error_log = _get_attr_safe(context, 'error_log', [])
    if not isinstance(error_log, list):
        error_log = []
    
    error_log.append(error_record)
    
    # 로그 크기 제한 (최근 100개만 유지)
    if len(error_log) > 100:
        error_log = error_log[-100:]
    
    _set_attr_safe(context, 'error_log', error_log)


def _track_file_operation(context, action: str, args: tuple, kwargs: dict):
    """파일 작업 추적"""
    if not context or not args:
        return
    
    # 파일 경로 추출
    file_path = args[0] if args else kwargs.get('path', kwargs.get('file_path', ''))
    
    # file_access_history에 기록
    file_access_history = _get_attr_safe(context, 'file_access_history', [])
    if not isinstance(file_access_history, list):
        file_access_history = []
    
    access_record = {
        'file': file_path,
        'operation': action,
        'timestamp': datetime.now().isoformat(),
        'task_id': _get_attr_safe(context, 'current_task')
    }
    
    file_access_history.append(access_record)
    
    # 히스토리 크기 제한
    if len(file_access_history) > 100:
        file_access_history = file_access_history[-100:]
    
    _set_attr_safe(context, 'file_access_history', file_access_history)
    
    # task_tracking에도 기록
    current_task = _get_attr_safe(context, 'current_task')
    metadata = _get_attr_safe(context, 'metadata', {})
    
    if current_task and isinstance(metadata, dict) and 'task_tracking' in metadata:
        task_tracking = metadata['task_tracking']
        if current_task in task_tracking:
            if action in ['create', 'modify', 'write']:
                # files_modified가 set인지 확인하고 아니면 set으로 변환
                if 'files_modified' not in task_tracking[current_task]:
                    task_tracking[current_task]['files_modified'] = set()
                elif not isinstance(task_tracking[current_task]['files_modified'], set):
                    # 문자열이나 리스트인 경우 set으로 변환
                    existing = task_tracking[current_task]['files_modified']
                    if isinstance(existing, str):
                        task_tracking[current_task]['files_modified'] = {existing} if existing else set()
                    elif isinstance(existing, list):
                        task_tracking[current_task]['files_modified'] = set(existing)
                    else:
                        task_tracking[current_task]['files_modified'] = set()
                
                task_tracking[current_task]['files_modified'].add(file_path)


def _track_code_operation(context, action: str, args: tuple, kwargs: dict):
    """코드 수정 작업 추적"""
    if not context or len(args) < 2:
        return
    
    file_path = args[0]
    block_name = args[1] if len(args) > 1 else kwargs.get('block_name', '')
    
    # function_edit_history에 기록
    function_edit_history = _get_attr_safe(context, 'function_edit_history', [])
    if not isinstance(function_edit_history, list):
        function_edit_history = []
    
    edit_record = {
        'file': file_path,
        'function': block_name,
        'operation': action,
        'timestamp': datetime.now().isoformat(),
        'task_id': _get_attr_safe(context, 'current_task')
    }
    
    function_edit_history.append(edit_record)
    
    # 히스토리 크기 제한
    if len(function_edit_history) > 50:
        function_edit_history = function_edit_history[-50:]
    
    _set_attr_safe(context, 'function_edit_history', function_edit_history)
    
    # task_tracking에도 기록
    current_task = _get_attr_safe(context, 'current_task')
    metadata = _get_attr_safe(context, 'metadata', {})
    
    if current_task and isinstance(metadata, dict) and 'task_tracking' in metadata:
        task_tracking = metadata['task_tracking']
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
