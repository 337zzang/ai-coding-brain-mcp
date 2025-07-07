"""파일 시스템 관련 헬퍼 함수들"""

from typing import Optional, List, Union
import os
import shutil
import tempfile
import time
import functools
from datetime import datetime
from ai_helpers.decorators import track_operation
from ai_helpers.context import get_project_context


# _atomic_write는 atomic_io 모듈 사용
from atomic_io import atomic_write as _atomic_write
import textwrap

@track_operation('file', 'create')
def create_file(file_path: str, content: str = '') -> str:
    """새 파일 생성
    
    Args:
        file_path: 생성할 파일 경로
        content: 파일 내용
        
    Returns:
        str: 성공/실패 메시지
    """
    try:
        _atomic_write(file_path, content, mode='text')
        return f'SUCCESS: 파일 생성 완료 - {file_path}'
    except Exception as e:
        return f'ERROR: 파일 생성 실패 - {e}'


@track_operation('file', 'read')
def read_file(file_path: str) -> str:
    """파일 내용을 읽어서 반환
    
    Args:
        file_path: 읽을 파일 경로
        
    Returns:
        str: 파일 내용
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        raise


@track_operation('file', 'write')
def write_file(file_path: str, content: str) -> str:
    """파일에 내용 쓰기 (덮어쓰기)"""
    try:
        _atomic_write(file_path, content, mode='text')
        return f'SUCCESS: 파일 쓰기 완료 - {file_path}'
    except Exception as e:
        return f'ERROR: 파일 쓰기 실패 - {e}'


@track_operation('file', 'append')
def append_to_file(file_path: str, content: str) -> str:
    """파일에 내용 추가"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing = f.read()
            _atomic_write(file_path, existing + content, mode='text')
        else:
            _atomic_write(file_path, content, mode='text')
        return f'SUCCESS: 파일 추가 완료 - {file_path}'
    except Exception as e:
        return f'ERROR: 파일 추가 실패 - {e}'


# Auto-tracking wrapper에서 이동된 함수들

def track_file_access(file_path, operation, details=None):
    """파일 접근 추적 헬퍼 함수"""
    context = get_project_context()
    
    if context and hasattr(context, 'tracking') and context.tracking:
        # 파일 접근 기록 업데이트
        if 'file_access' not in context.tracking:
            context.tracking['file_access'] = {}
        
        if file_path not in context.tracking['file_access']:
            context.tracking['file_access'][file_path] = {
                'first_access': datetime.now().isoformat(),
                'operations': []
            }
        
        context.tracking['file_access'][file_path]['operations'].append({
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'details': details
        })


def track_file_operation(operation_type: str):
    """파일 작업 추적 데코레이터 - Task 연동 개선"""
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = get_project_context()
            
            # 파일 경로 추출
            file_path = args[0] if args else kwargs.get('file_path', 'unknown')
            
            # 시작 시간 기록
            start_time = time.time()
            
            try:
                # 원래 함수 실행
                result = func(*args, **kwargs)
                
                # 성공 기록
                if context and hasattr(context, 'tracking'):
                    # Task 관련 추적
                    if hasattr(context, 'current_task') and context.current_task:
                        task_id = context.current_task
                        if 'task_tracking' not in context.tracking:
                            context.tracking['task_tracking'] = {}
                        
                        if task_id not in context.tracking['task_tracking']:
                            context.tracking['task_tracking'][task_id] = {
                                'files_accessed': [],
                                'files_modified': [],
                                'operations': []
                            }
                        
                        task_tracking = context.tracking['task_tracking'][task_id]
                        
                        # 파일 추적
                        if operation_type in ['create', 'write', 'append']:
                            if file_path not in task_tracking['files_modified']:
                                task_tracking['files_modified'].append(file_path)
                        elif operation_type == 'read':
                            if file_path not in task_tracking['files_accessed']:
                                task_tracking['files_accessed'].append(file_path)
                        
                        # 작업 기록
                        task_tracking['operations'].append({
                            'type': f'file_{operation_type}',
                            'file': file_path,
                            'timestamp': datetime.now().isoformat(),
                            'duration': time.time() - start_time
                        })
                
                return result
                
            except Exception as e:
                # 실패 기록
                if context and hasattr(context, 'tracking'):
                    if 'errors' not in context.tracking:
                        context.tracking['errors'] = []
                    
                    context.tracking['errors'].append({
                        'operation': f'file_{operation_type}',
                        'file': file_path,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                
                raise
        
        return wrapper
    
    return decorator