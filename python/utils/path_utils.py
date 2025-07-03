"""
통합된 경로 유틸리티 모듈
여러 곳에 분산되어 있던 path_utils를 하나로 통합
"""
import os
from pathlib import Path
from typing import Optional, Union


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    current = Path(__file__).resolve()
    
    # .git 폴더나 pyproject.toml을 찾아 올라감
    while current != current.parent:
        if (current / '.git').exists() or (current / 'pyproject.toml').exists():
            return current
        current = current.parent
    
    # 못 찾으면 python 폴더의 부모를 반환
    return Path(__file__).resolve().parent.parent


def ensure_dir(path: Union[str, Path]) -> Path:
    """디렉토리가 없으면 생성하고 Path 객체 반환"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_memory_dir() -> Path:
    """memory 디렉토리 경로 반환 (없으면 생성)"""
    memory_dir = get_project_root() / "memory"
    return ensure_dir(memory_dir)


def get_memory_path(filename: str = "workflow.json") -> Path:
    """memory 디렉토리 내 파일 경로 반환"""
    return get_memory_dir() / filename


def get_context_path() -> Path:
    """context.json 파일 경로 반환"""
    return get_memory_dir() / "context.json"


def get_cache_dir() -> Path:
    """캐시 디렉토리 경로 반환 (없으면 생성)"""
    cache_dir = get_memory_dir() / "cache"
    return ensure_dir(cache_dir)


def get_file_directory_cache_path() -> Path:
    """파일 디렉토리 캐시 경로 반환"""
    return get_cache_dir() / "file_directory.json"


def safe_relative_path(path: Union[str, Path], base: Optional[Union[str, Path]] = None) -> str:
    """안전한 상대 경로 반환"""
    try:
        path = Path(path).resolve()
        base = Path(base).resolve() if base else get_project_root()
        return str(path.relative_to(base))
    except (ValueError, RuntimeError):
        return str(path)


def find_git_root(start_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Git 저장소 루트 찾기"""
    current = Path(start_path or os.getcwd()).resolve()
    
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    
    return None


def verify_git_root(path: Union[str, Path]) -> bool:
    """주어진 경로가 Git 저장소 루트인지 확인"""
    path = Path(path)
    return (path / '.git').exists()


# Desktop 관련 함수는 프로젝트에 특화되어 있으므로 제외
# ensure_project_directory는 프로젝트 초기화 관련이므로 별도 모듈로
