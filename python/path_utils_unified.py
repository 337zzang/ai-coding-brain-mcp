"""
통합된 프로젝트 경로 관리 유틸리티
환경변수와 Desktop 처리를 모두 지원하는 단일 모듈
"""
import os
from pathlib import Path
from typing import Optional

def get_desktop_path() -> Path:
    """사용자의 바탕화면 경로를 반환합니다."""
    if os.name == 'nt':
        return Path(os.environ['USERPROFILE']) / 'Desktop'
    else:
        return Path.home() / 'Desktop'

def get_project_root(project_name: Optional[str] = None) -> Path:
    """프로젝트 루트 경로를 반환합니다.

    우선순위:
    1. FLOW_PROJECT_ROOT 환경변수
    2. AI_PROJECTS_DIR 환경변수
    3. 현재 디렉토리가 Desktop의 하위면 현재 디렉토리
    4. ~/Desktop (기본값)

    Args:
        project_name: 프로젝트 이름. None이면 현재 디렉토리 기준
    """
    # 환경변수 확인
    root = os.environ.get('FLOW_PROJECT_ROOT')
    if not root:
        root = os.environ.get('AI_PROJECTS_DIR')

    # 환경변수가 없는 경우
    if not root:
        current = Path.cwd()
        desktop = get_desktop_path()

        # 현재 디렉토리가 Desktop의 하위인 경우
        if desktop in current.parents or current == desktop:
            if project_name is None:
                return current
            # 프로젝트명이 지정된 경우 Desktop 기준
            root = str(desktop)
        else:
            # Desktop이 아닌 경우 현재 디렉토리 사용
            if project_name is None:
                return current
            root = str(desktop)  # 기본값은 Desktop

    root_path = Path(root)

    if project_name:
        return root_path / project_name
    return root_path

def ensure_dir(path: Path) -> Path:
    """디렉토리가 존재하도록 보장합니다."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def ensure_project_directory(project_name: str) -> Path:
    """프로젝트 디렉토리 확인 및 생성"""
    project_path = get_project_root(project_name)
    project_path.mkdir(parents=True, exist_ok=True)

    # 필수 서브디렉토리 생성
    subdirs = ['memory', 'memory/cache', 'memory/backup', 
               'test', 'docs', 'src']
    for subdir in subdirs:
        (project_path / subdir).mkdir(parents=True, exist_ok=True)

    return project_path

# --- 프로젝트별 경로 함수 ---
def get_memory_dir(project_name: Optional[str] = None) -> Path:
    """프로젝트의 memory 디렉토리 경로를 반환합니다."""
    return ensure_dir(get_project_root(project_name) / "memory")

def get_context_path(project_name: Optional[str] = None) -> Path:
    """프로젝트의 context.json 경로를 반환합니다."""
    memory_dir = get_memory_dir(project_name)
    # 새로운 구조 우선 확인
    active_path = memory_dir / "active" / "context.json"
    if active_path.exists():
        return active_path
    # 기존 경로 fallback
    return memory_dir / "context.json"

def get_workflow_path(project_name: Optional[str] = None) -> Path:
    """프로젝트의 workflow.json 경로를 반환합니다."""
    memory_dir = get_memory_dir(project_name)
    # 새로운 구조 우선 확인
    active_path = memory_dir / "active" / "workflow.json"
    if active_path.exists():
        return active_path
    # 기존 경로 fallback
    return memory_dir / "workflow.json"

def get_cache_dir(project_name: Optional[str] = None) -> Path:
    """프로젝트의 캐시 디렉토리를 반환합니다."""
    return ensure_dir(get_memory_dir(project_name) / "cache")

def get_backup_dir(project_name: Optional[str] = None) -> Path:
    """프로젝트의 백업 디렉토리를 반환합니다."""
    return ensure_dir(get_memory_dir(project_name) / "backup")

def get_file_directory_cache_path(project_name: Optional[str] = None) -> Path:
    """file_directory.json 캐시 파일 경로를 반환합니다."""
    return get_cache_dir(project_name) / "file_directory.json"

def get_memory_path(filename: str, project_name: Optional[str] = None) -> Path:
    """메모리 파일 경로 가져오기 (호환성 유지)"""
    return get_memory_dir(project_name) / filename

# workflow_v3 관련 경로 (이후 제거 예정)
def get_workflow_v3_dir() -> Path:
    """DEPRECATED: workflow_v3 디렉토리 경로 (마이그레이션 후 제거)"""
    return ensure_dir(Path.cwd() / "memory" / "workflow_v3")
