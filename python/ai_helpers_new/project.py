"""
프로젝트 관리 및 전환 기능
리팩토링: 2025-08-02
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from .util import ok, err
from .core.fs import scan_directory as core_scan_directory, ScanOptions

# Workflow manager import (optional)
try:
    from python.workflow_wrapper import get_workflow_manager
except ImportError:
    def get_workflow_manager():
        return None

# 전역 캐시
_current_project_cache = None

def _read_if_exists(path: str, max_lines: int = 80) -> Optional[str]:
    """파일이 존재하면 앞 max_lines 줄만 읽어 문자열 반환"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return ''.join(lines)
    except IOError:
        return None

def get_current_project() -> dict:
    """현재 프로젝트 정보 가져오기"""
    global _current_project_cache

    if _current_project_cache is not None:
        return ok(_current_project_cache)

    try:
        cwd = os.getcwd()
        project_name = os.path.basename(cwd)

        # 프로젝트 타입 판별
        if os.path.exists(os.path.join(cwd, "package.json")):
            project_type = "node"
        elif os.path.exists(os.path.join(cwd, "requirements.txt")) or os.path.exists(os.path.join(cwd, "setup.py")):
            project_type = "python"
        else:
            project_type = "unknown"

        project_info = {
            "name": project_name,
            "path": cwd,
            "type": project_type,
            "has_git": os.path.exists(os.path.join(cwd, ".git"))
        }

        _current_project_cache = project_info
        return ok(project_info)

    except Exception as e:
        return err(str(e))

def flow_project_with_workflow(
    project: str,
    *,
    auto_read_docs: bool = True,
    readme_lines: int = 60,
    file_dir_lines: int = 120
) -> Dict[str, Any]:
    """
    프로젝트 전환 & 워크플로우 초기화 + README / file_directory 자동 출력

    Parameters
    ----------
    project : str
        프로젝트 디렉토리 이름 (바탕화면에서 검색)
    auto_read_docs : bool
        True 이면 README.md 와 file_directory.md 를 자동 출력
    readme_lines / file_dir_lines : int
        각각 출력할 최대 줄 수
    """
    # 1) 바탕화면에서 프로젝트 찾기
    desktop_path = Path.home() / "Desktop"
    if not desktop_path.exists():
        desktop_path = Path.home() / "바탕화면"

    if not desktop_path.exists():
        return err("❌ 바탕화면 경로를 찾을 수 없습니다")

    project_path = desktop_path / project
    if not project_path.exists() or not project_path.is_dir():
        print(f"❌ 프로젝트를 찾을 수 없습니다: {project}")
        print(f"   검색 경로: {desktop_path}")
        return err(f"프로젝트를 찾을 수 없습니다: {project}")

    # 2) 디렉토리 이동
    try:
        previous_dir = os.getcwd()
        os.chdir(str(project_path))
    except OSError as e:
        return err(f"디렉토리 이동 실패: {e}")

    # 캐시 리셋
    global _current_project_cache
    _current_project_cache = None

    # 3) 프로젝트 정보 수집
    proj_info = get_current_project()
    if not proj_info['ok']:
        return proj_info

    # 캐시 파일 업데이트
    try:
        cache_dir = Path.home() / ".ai-coding-brain" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_data = proj_info['data'].copy()
        cache_data['switched_at'] = datetime.now().isoformat()

        with open(cache_dir / "current_project.json", 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except:
        pass  # 캐시 실패는 무시

    # 4) 기본 정보 출력
    print(f"✅ 프로젝트 전환: {project}")
    print(f"📍 경로: {project_path}")
    print(f"📁 Flow 저장소: {project}/.ai-brain/flow/")

    # 5) 문서 자동 읽기
    docs: Dict[str, str] = {}
    if auto_read_docs:
        readme_txt = _read_if_exists(str(project_path / "readme.md"), readme_lines)
        if readme_txt:
            docs["readme.md"] = readme_txt
            print("\n📖 README.md 내용:")
            print("=" * 70)
            print(readme_txt)

        fd_txt = _read_if_exists(str(project_path / "file_directory.md"), file_dir_lines)
        if fd_txt:
            docs["file_directory.md"] = fd_txt
            print("\n📁 프로젝트 구조 (file_directory.md):")
            print("=" * 70)
            print(fd_txt)

    # 6) Git 상태
    git_info = None
    try:
        from .git import git_status
        git_result = git_status()
        if git_result['ok']:
            git_info = git_result['data']
            print("\n🔀 Git 상태:")
            print("=" * 70)
            print(f"브랜치: {git_info['branch']}")
            print(f"변경 파일: {git_info['count']}개")
            print(f"상태: {'Clean' if git_info['clean'] else 'Modified'}")
    except:
        pass

    # 7) Flow 상태
    flow_info = None
    try:
        from .simple_flow_commands import flow as flow_cmd
        flow_status = flow_cmd("/status")
        if flow_status and flow_status.get('ok'):
            flow_info = flow_status.get('data')
            # Flow 상태는 이미 출력되므로 추가 출력 불필요
    except:
        pass

    # 8) 결과 반환
    return ok(
        {
            "project": proj_info['data'],
            "previous": previous_dir,
            "docs": docs,
            "git": git_info,
            "flow": flow_info
        },
        msg=f"🚀 프로젝트 전환 완료: {project}"
    )

# 나머지 함수들은 그대로 유지
def scan_directory(path: str = ".", output: str = "list", max_depth: int = None, exclude_patterns: List[str] = None) -> Any:
    """디렉토리 스캔 (core 모듈 사용)"""
    try:
        options = ScanOptions(
            max_depth=max_depth,
            exclude_patterns=exclude_patterns,
            output_format=output
        )
        return core_scan_directory(path, options)
    except Exception as e:
        if output == "list":
            return []
        return {}


def scan_directory_dict(path: str = ".", max_depth: int = 5, 
                       ignore_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
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

    def scan_recursive(dir_path: str, current_depth: int = 0) -> Dict[str, Any]:
        if current_depth >= max_depth:
            return {'type': 'directory', 'children': {}}

        result = {'type': 'directory', 'children': {}}

        try:
            for item in os.listdir(dir_path):
                if should_ignore(item):
                    continue

                item_path = os.path.join(dir_path, item)

                if os.path.isfile(item_path):
                    result['children'][item] = {
                        'type': 'file',
                        'size': os.path.getsize(item_path)
                    }
                elif os.path.isdir(item_path):
                    result['children'][item] = scan_recursive(item_path, current_depth + 1)
        except PermissionError:
            pass

        return result

    root_path = os.path.abspath(path)
    structure = scan_recursive(root_path)

    # 통계 계산
    total_files = 0
    total_dirs = 0

    def count_items(node):
        nonlocal total_files, total_dirs
        if node.get('type') == 'file':
            total_files += 1
        elif node.get('type') == 'directory':
            total_dirs += 1
            if 'children' in node:
                for child in node['children'].values():
                    count_items(child)

    count_items(structure)

    return {
        'root': root_path,
        'structure': structure.get('children', {}),
        'stats': {
            'total_files': total_files,
            'total_dirs': total_dirs
        }
    }

