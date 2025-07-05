"""
원자적 파일 I/O 유틸리티
동시성 안전 파일 읽기/쓰기
"""
import os
import json
import tempfile
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from functools import wraps
import threading
import time

logger = logging.getLogger(__name__)

# 파일별 락 관리
_file_locks = {}
_lock_manager = threading.Lock()

def get_file_lock(filepath: str) -> threading.Lock:
    """파일별 락 가져오기"""
    with _lock_manager:
        if filepath not in _file_locks:
            _file_locks[filepath] = threading.Lock()
        return _file_locks[filepath]

def atomic_write(filepath: str, data: Any, mode: str = 'json') -> bool:
    """원자적 파일 쓰기
    
    Args:
        filepath: 대상 파일 경로
        data: 저장할 데이터
        mode: 'json' 또는 'text'
        
    Returns:
        성공 여부
    """
    filepath = Path(filepath)
    lock = get_file_lock(str(filepath))
    
    with lock:
        try:
            # 디렉토리 생성
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 임시 파일에 쓰기
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=filepath.parent,
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                if mode == 'json':
                    json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                else:
                    tmp_file.write(str(data))
                tmp_path = tmp_file.name
            
            # 원자적 교체 (Windows에서는 기존 파일 삭제 필요)
            if os.name == 'nt' and filepath.exists():
                filepath.unlink()
            
            # 임시 파일을 대상 경로로 이동
            os.rename(tmp_path, filepath)
            
            logger.debug(f"원자적 쓰기 성공: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"원자적 쓰기 실패 {filepath}: {e}")
            # 임시 파일 정리
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            return False

def safe_read(filepath: str, mode: str = 'json', default: Any = None) -> Any:
    """안전한 파일 읽기
    
    Args:
        filepath: 파일 경로
        mode: 'json' 또는 'text'
        default: 파일이 없거나 오류 시 반환할 기본값
        
    Returns:
        파일 내용 또는 기본값
    """
    filepath = Path(filepath)
    lock = get_file_lock(str(filepath))
    
    with lock:
        try:
            if not filepath.exists():
                return default
                
            with open(filepath, 'r', encoding='utf-8') as f:
                if mode == 'json':
                    return json.load(f)
                else:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"파일 읽기 실패 {filepath}: {e}")
            return default

def safe_io(func):
    """안전한 I/O 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"I/O 오류 in {func.__name__}")
            # HelperResult 형식으로 반환
            return {
                'ok': False,
                'error': f"I/O Error: {str(e)}",
                'data': None
            }
    return wrapper

# 컨텍스트/워크플로우 전용 헬퍼
def save_context(context: Dict[str, Any], project_name: Optional[str] = None) -> bool:
    """컨텍스트 저장"""
    from path_utils import get_memory_path
    filepath = get_memory_path('context.json', project_name)
    return atomic_write(filepath, context)

def load_context(project_name: Optional[str] = None) -> Dict[str, Any]:
    """컨텍스트 로드"""
    from path_utils import get_memory_path
    filepath = get_memory_path('context.json', project_name)
    return safe_read(filepath, default={})

def save_workflow(workflow_data: Dict[str, Any], project_name: Optional[str] = None) -> bool:
    """워크플로우 저장"""
    from path_utils import get_memory_path
    filepath = get_memory_path('workflow.json', project_name)
    return atomic_write(filepath, workflow_data)

def load_workflow(project_name: Optional[str] = None) -> Dict[str, Any]:
    """워크플로우 로드"""
    from path_utils import get_memory_path
    filepath = get_memory_path('workflow.json', project_name)
    return safe_read(filepath, default={'plans': [], 'current_plan_id': None})
