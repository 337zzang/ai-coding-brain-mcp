"""
프로젝트 관리 - 프로토콜 추적 포함
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .core import track_execution
from .file_ops import read_json, write_json, file_exists

@track_execution
def get_current_project() -> Dict[str, Any]:
    """현재 프로젝트 정보 가져오기"""
    # 프로젝트 루트 찾기
    current_dir = Path.cwd()

    # Git 디렉토리 찾기
    git_dir = None
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / '.git').exists():
            git_dir = parent
            break

    project_root = git_dir or current_dir
    project_name = project_root.name

    # 프로젝트 타입 감지
    project_type = detect_project_type(project_root)

    return {
        'name': project_name,
        'path': str(project_root),
        'type': project_type,
        'has_git': git_dir is not None
    }

def detect_project_type(project_root: Path) -> str:
    """프로젝트 타입 감지"""
    if (project_root / 'package.json').exists():
        return 'node'
    elif (project_root / 'requirements.txt').exists() or (project_root / 'setup.py').exists():
        return 'python'
    elif (project_root / 'Cargo.toml').exists():
        return 'rust'
    elif (project_root / 'go.mod').exists():
        return 'go'
    else:
        return 'unknown'

@track_execution
def scan_directory_dict(
    path: str = ".",
    max_depth: int = 5,
    ignore_patterns: List[str] = None
) -> Dict[str, Any]:
    """디렉토리 구조를 딕셔너리로 스캔"""
    if ignore_patterns is None:
        ignore_patterns = [
            '__pycache__', '.git', 'node_modules',
            '.pytest_cache', '.venv', 'venv',
            '*.pyc', '*.pyo', '.DS_Store'
        ]

    def should_ignore(name: str) -> bool:
        for pattern in ignore_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True
        return False

    def scan_recursive(current_path: Path, current_depth: int) -> Dict[str, Any]:
        if current_depth > max_depth:
            return {'type': 'directory', 'contents': {}}

        result = {}

        try:
            for item in current_path.iterdir():
                if should_ignore(item.name):
                    continue

                if item.is_file():
                    result[item.name] = {
                        'type': 'file',
                        'size': item.stat().st_size,
                        'modified': item.stat().st_mtime
                    }
                elif item.is_dir():
                    result[item.name] = {
                        'type': 'directory',
                        'contents': scan_recursive(item, current_depth + 1)
                    }
        except PermissionError:
            pass

        return result

    root_path = Path(path)
    structure = scan_recursive(root_path, 0)

    # 통계 계산
    total_files = 0
    total_dirs = 0
    total_size = 0

    def count_items(items: Dict[str, Any]):
        nonlocal total_files, total_dirs, total_size
        for name, info in items.items():
            if info['type'] == 'file':
                total_files += 1
                total_size += info.get('size', 0)
            else:
                total_dirs += 1
                count_items(info.get('contents', {}))

    count_items(structure)

    return {
        'root': str(root_path.absolute()),
        'structure': structure,
        'stats': {
            'total_files': total_files,
            'total_directories': total_dirs,
            'total_size': total_size
        }
    }

@track_execution
def create_project_structure(
    project_name: str,
    project_type: str = 'python',
    base_path: str = "."
) -> Dict[str, Any]:
    """프로젝트 기본 구조 생성"""
    project_path = Path(base_path) / project_name

    # 디렉토리 생성
    project_path.mkdir(parents=True, exist_ok=True)

    # 프로젝트 타입별 구조 생성
    if project_type == 'python':
        # Python 프로젝트 구조
        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'tests').mkdir(exist_ok=True)
        (project_path / 'docs').mkdir(exist_ok=True)

        # 기본 파일들
        (project_path / 'README.md').write_text(f"# {project_name}\n\nProject description here.")
        (project_path / 'requirements.txt').write_text("")
        (project_path / '.gitignore').write_text("__pycache__/\n*.pyc\n.venv/\nvenv/\n.env")

    elif project_type == 'node':
        # Node.js 프로젝트 구조
        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'tests').mkdir(exist_ok=True)

        # package.json
        package_json = {
            "name": project_name,
            "version": "1.0.0",
            "description": "",
            "main": "index.js",
            "scripts": {
                "test": "echo \"Error: no test specified\" && exit 1"
            }
        }
        write_json(str(project_path / 'package.json'), package_json)

    return {
        'success': True,
        'project_path': str(project_path),
        'created_files': list(project_path.rglob('*'))
    }

# 사용 가능한 함수 목록
__all__ = [
    'get_current_project', 'scan_directory_dict',
    'create_project_structure'
]
