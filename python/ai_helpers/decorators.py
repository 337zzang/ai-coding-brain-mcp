"""공통 데코레이터 모듈 - 향상된 버전"""

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
                
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if debug:
                    print(f"❌ {operation_type}:{action} 실패 ({execution_time:.2f}초): {e}")
                
                # 실패 추적
                _track_error(context, operation_type, action, e, args, kwargs, execution_time)
                
                raise
        
        return wrapper
    return decorator


def _track_success(context, operation_type: str, action: str, args: tuple, kwargs: dict, result: Any, execution_time: float):
    """작업 성공 추적"""
    if not context:
        return
        
    # 현재 태스크 가져오기
    current_task = context.current_task
    if not current_task:
        return
    
    # task_tracking이 metadata에 있는지 확인
    if 'task_tracking' not in context.metadata:
        context.metadata['task_tracking'] = {}
    
    task_tracking = context.metadata['task_tracking']
    
    # 현재 태스크의 추적 정보가 없으면 생성
    if current_task not in task_tracking:
        task_tracking[current_task] = {
            'operations': [],
            'files_modified': set(),
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
    
    if not hasattr(context, 'error_log') or context.error_log is None:
        context.error_log = []
    
    context.error_log.append(error_record)
    
    # 로그 크기 제한 (최근 100개만 유지)
    if len(context.error_log) > 100:
        context.error_log = context.error_log[-100:]


def _track_file_operation(context, action: str, args: tuple, kwargs: dict):
    """파일 작업 추적"""
    if not context or not args:
        return
    
    # 파일 경로 추출
    file_path = args[0] if args else kwargs.get('path', kwargs.get('file_path', ''))
    
    # file_access_history에 기록
    if context.file_access_history is None:
        context.file_access_history = []
    
    access_record = {
        'file': file_path,
        'operation': action,
        'timestamp': datetime.now().isoformat(),
        'task_id': context.current_task
    }
    
    context.file_access_history.append(access_record)
    
    # 히스토리 크기 제한
    if len(context.file_access_history) > 100:
        context.file_access_history = context.file_access_history[-100:]
    
    # task_tracking에도 기록
    if context.current_task and 'task_tracking' in context.metadata:
        task_tracking = context.metadata['task_tracking']
        if context.current_task in task_tracking:
            if action in ['create', 'modify', 'write']:
                task_tracking[context.current_task]['files_modified'].add(file_path)


def _track_code_operation(context, action: str, args: tuple, kwargs: dict):
    """코드 수정 작업 추적"""
    if not context or len(args) < 2:
        return
    
    file_path = args[0]
    block_name = args[1] if len(args) > 1 else kwargs.get('block_name', '')
    
    # function_edit_history에 기록
    if context.function_edit_history is None:
        context.function_edit_history = []
    
    edit_record = {
        'file': file_path,
        'function': block_name,
        'operation': action,
        'timestamp': datetime.now().isoformat(),
        'task_id': context.current_task
    }
    
    context.function_edit_history.append(edit_record)
    
    # 히스토리 크기 제한
    if len(context.function_edit_history) > 50:
        context.function_edit_history = context.function_edit_history[-50:]
    
    # task_tracking에도 기록
    if context.current_task and 'task_tracking' in context.metadata:
        task_tracking = context.metadata['task_tracking']
        if context.current_task in task_tracking:
            task_tracking[context.current_task]['functions_edited'].add(f'{file_path}::{block_name}')


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
        module = importlib.import_module(module_name)
        func = getattr(module, function_name)
        return func(*args, **kwargs)
    
    lazy_wrapper.__name__ = function_name
    lazy_wrapper.__doc__ = f"Lazy-loaded from {module_name}.{function_name}"
    
    return lazy_wrapper
