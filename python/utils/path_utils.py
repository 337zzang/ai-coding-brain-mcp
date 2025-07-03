"""
Path utilities for project and git directory management
"""
import os
from pathlib import Path
from typing import Optional, Union


def get_project_root(project_name: Optional[str] = None) -> Path:
    """
    프로젝트 루트 디렉토리 경로 반환
    
    Args:
        project_name: 프로젝트 이름 (None이면 현재 디렉토리)
        
    Returns:
        프로젝트 루트 경로 (절대경로)
    """
    if project_name:
        # 프로젝트 이름이 주어진 경우, 상위 디렉토리에서 찾기
        base_dir = Path.cwd().parent
        project_path = base_dir / project_name
        if project_path.exists():
            return project_path.resolve()
    
    # 현재 디렉토리 반환
    return Path.cwd().resolve()


def verify_git_root(path: Union[str, Path]) -> Path:
    """
    Git 저장소 루트인지 검증
    
    Args:
        path: 검증할 경로
        
    Returns:
        검증된 절대 경로
        
    Raises:
        ValueError: .git 디렉토리가 없는 경우
    """
    path = Path(path).resolve()
    git_dir = path / '.git'
    
    if not git_dir.exists():
        raise ValueError(f"Not a git repository: {path}")
    
    return path


def find_git_root(start_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """
    현재 경로부터 상위로 올라가며 Git 저장소 루트 찾기
    
    Args:
        start_path: 시작 경로 (None이면 현재 디렉토리)
        
    Returns:
        Git 저장소 루트 경로 또는 None
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)
    
    current = start_path.resolve()
    
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    
    # 루트 디렉토리에도 .git이 있는지 확인
    if (current / '.git').exists():
        return current
    
    return None


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    디렉토리가 존재하지 않으면 생성
    
    Args:
        path: 디렉토리 경로
        
    Returns:
        생성된 또는 기존 디렉토리 경로
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def safe_relative_path(path: Union[str, Path], base: Optional[Union[str, Path]] = None) -> str:
    """
    안전한 상대 경로 반환
    
    Args:
        path: 대상 경로
        base: 기준 경로 (None이면 현재 디렉토리)
        
    Returns:
        상대 경로 문자열
    """
    path = Path(path).resolve()
    base = Path(base).resolve() if base else Path.cwd().resolve()
    
    try:
        return str(path.relative_to(base))
    except ValueError:
        # 상대 경로로 표현할 수 없는 경우 절대 경로 반환
        return str(path)
