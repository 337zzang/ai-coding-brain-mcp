"""
경로 유틸리티 함수들
ai-coding-brain-mcp 프로젝트용
"""

import os
from pathlib import Path
from typing import Union, Optional


def normalize_path(path: Union[str, Path]) -> Path:
    """경로를 정규화하여 Path 객체로 반환"""
    return Path(path).resolve()


def ensure_directory(path: Union[str, Path]) -> Path:
    """디렉토리가 존재하지 않으면 생성"""
    path = normalize_path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_relative_path(target: Union[str, Path], base: Union[str, Path] = None) -> Path:
    """기준 경로에서 대상 경로까지의 상대 경로 반환"""
    if base is None:
        base = Path.cwd()

    target = normalize_path(target)
    base = normalize_path(base)

    try:
        return target.relative_to(base)
    except ValueError:
        # 상대 경로로 표현할 수 없는 경우 절대 경로 반환
        return target


def safe_path_join(*parts) -> Path:
    """안전한 경로 결합"""
    if not parts:
        return Path.cwd()

    result = Path(parts[0])
    for part in parts[1:]:
        result = result / part

    return normalize_path(result)


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 찾기"""
    current = Path.cwd()

    # .git 디렉토리나 특정 파일들을 찾아서 프로젝트 루트 결정
    indicators = ['.git', 'README.md', 'requirements.txt', 'python']

    while current.parent != current:  # 루트까지 올라가지 않도록
        for indicator in indicators:
            if (current / indicator).exists():
                return current
        current = current.parent

    # 찾지 못한 경우 현재 디렉토리 반환
    return Path.cwd()


def ensure_file_directory(file_path: Union[str, Path]) -> Path:
    """파일의 디렉토리가 존재하지 않으면 생성"""
    file_path = normalize_path(file_path)
    if file_path.parent != file_path:  # 루트가 아닌 경우
        ensure_directory(file_path.parent)
    return file_path


def is_subdirectory(child: Union[str, Path], parent: Union[str, Path]) -> bool:
    """child가 parent의 하위 디렉토리인지 확인"""
    try:
        child = normalize_path(child)
        parent = normalize_path(parent)
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def get_file_size(file_path: Union[str, Path]) -> int:
    """파일 크기 반환 (bytes)"""
    file_path = normalize_path(file_path)
    try:
        return file_path.stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def list_files_recursive(directory: Union[str, Path], pattern: str = "*") -> list[Path]:
    """디렉토리에서 패턴에 맞는 파일들을 재귀적으로 찾기"""
    directory = normalize_path(directory)
    if not directory.is_dir():
        return []

    try:
        return list(directory.rglob(pattern))
    except (OSError, PermissionError):
        return []


def backup_file(file_path: Union[str, Path], backup_suffix: str = ".backup") -> Optional[Path]:
    """파일 백업 생성"""
    file_path = normalize_path(file_path)

    if not file_path.exists():
        return None

    backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)

    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    except (OSError, PermissionError):
        return None


def ensure_dir(path: Union[str, Path]) -> Path:
    """디렉토리 생성 (ensure_directory와 동일)"""
    return ensure_directory(path)


def safe_relative_path(target: Union[str, Path], base: Union[str, Path] = None) -> str:
    """안전한 상대 경로 반환 (문자열)"""
    rel_path = get_relative_path(target, base)
    return str(rel_path)


def verify_git_root(path: Union[str, Path] = None) -> bool:
    """Git 루트 디렉토리인지 확인"""
    if path is None:
        path = Path.cwd()
    else:
        path = normalize_path(path)

    return (path / '.git').exists()


def write_gitignore(directory: Union[str, Path], patterns: list[str]) -> bool:
    """gitignore 파일 작성"""
    try:
        directory = normalize_path(directory)
        gitignore_path = directory / '.gitignore'

        with open(gitignore_path, 'w', encoding='utf-8') as f:
            for pattern in patterns:
                f.write(f"{pattern}\n")

        return True
    except Exception:
        return False


def is_git_available(*args, **kwargs):
    """is_git_available 함수 (플레이스홀더)"""
    return None


def find_git_root(start_path: Union[str, Path] = None) -> Optional[Path]:
    """Git 루트 디렉토리 찾기"""
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = normalize_path(start_path)

    current = start_path
    while current.parent != current:  # 루트까지
        if (current / '.git').exists():
            return current
        current = current.parent

    return None
