"""
프로젝트 경로 관리를 위한 유틸리티 모듈
모든 경로는 이 모듈을 통해 접근해야 합니다.
"""
import os
from pathlib import Path

def get_desktop_path() -> Path:
    """사용자의 바탕화면 경로를 반환합니다."""
    if os.name == 'nt':
        return Path(os.environ['USERPROFILE']) / 'Desktop'
    else:
        return Path.home() / 'Desktop'

def get_project_root(project_name: str = None) -> Path:
    """프로젝트 루트 경로를 반환합니다.
    
    Args:
        project_name: 프로젝트 이름. None이면 현재 디렉토리명 사용
    """
    if project_name is None:
        current = Path.cwd()
        if get_desktop_path() in current.parents:
            project_name = current.name
        else:
            # 바탕화면이 아니어도 현재 디렉토리 사용
            return current
    
    return get_desktop_path() / project_name

def ensure_dir(path: Path) -> Path:
    """디렉토리가 존재하도록 보장합니다."""
    path.mkdir(parents=True, exist_ok=True)
    return path

# --- 프로젝트별 경로 함수 ---
def get_memory_dir(project_name: str = None) -> Path:
    """프로젝트의 memory 디렉토리 경로를 반환합니다."""
    return ensure_dir(get_project_root(project_name) / "memory")

def get_context_path(project_name: str = None) -> Path:
    """프로젝트의 context.json 경로를 반환합니다."""
    return get_memory_dir(project_name) / "context.json"

def get_workflow_path(project_name: str = None) -> Path:
    """프로젝트의 workflow.json 경로를 반환합니다."""  
    return get_memory_dir(project_name) / "workflow.json"

def get_cache_dir(project_name: str = None) -> Path:
    """프로젝트의 캐시 디렉토리를 반환합니다."""
    return ensure_dir(get_memory_dir(project_name) / "cache")

def get_file_directory_cache_path(project_name: str = None) -> Path:
    """file_directory.json 캐시 파일 경로를 반환합니다."""
    return get_cache_dir(project_name) / "file_directory.json"
