"""
프로젝트 관리 및 전환 기능
리팩토링: 2025-08-02
"""
import os
import platform
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from .util import ok, err
from .wrappers import safe_execution
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

@safe_execution
def get_current_project() -> dict:
    """현재 프로젝트 정보 가져오기 (Session 기반)"""
    from .session import get_current_session

    global _current_project_cache

    # Session에서 프로젝트 정보 가져오기
    session = get_current_session()

    # Session이 초기화되지 않았으면 현재 디렉토리 기반으로 초기화
    if not session.is_initialized:
        cwd = os.getcwd()
        project_name = os.path.basename(cwd)
        try:
            session.set_project(project_name, cwd)
        except Exception as e:
            return err(f"프로젝트 초기화 실패: {e}")

    # 프로젝트 정보 가져오기
    project_ctx = session.project_context
    if not project_ctx:
        return err("프로젝트가 설정되지 않았습니다")

    # 캐시 확인
    project_path = str(project_ctx.base_path)
    if _current_project_cache and _current_project_cache.get('path') == project_path:
        return ok(_current_project_cache)

    try:
        # 프로젝트 정보 수집
        project_info = project_ctx.get_project_info()

        # 추가 정보 수집
        # Git 정보
        has_git = (project_ctx.base_path / ".git").exists()

        # Python 프로젝트 정보
        has_requirements = (project_ctx.base_path / "requirements.txt").exists()
        has_setup_py = (project_ctx.base_path / "setup.py").exists()
        has_pyproject = (project_ctx.base_path / "pyproject.toml").exists()

        # Node.js 프로젝트 정보
        has_package_json = (project_ctx.base_path / "package.json").exists()

        # 프로젝트 정보 구성
        result = {
            'name': project_info['name'],
            'path': project_info['path'],
            'type': project_info['type'],
            'has_git': has_git,
            'has_requirements': has_requirements,
            'has_setup_py': has_setup_py,
            'has_pyproject': has_pyproject,
            'has_package_json': has_package_json,
            'has_flow': project_info['has_flow']
        }

        # 캐시 업데이트
        _current_project_cache = result

        return ok(result)

    except Exception as e:
        return err(f"프로젝트 정보 수집 실패: {str(e)}")
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
def _get_project_search_paths() -> List[Path]:
    """프로젝트 검색 경로 목록 반환 (환경변수 우선)"""
    paths = []

    # 1. 환경변수 확인
    env_path = os.environ.get("PROJECT_BASE_PATH")
    if env_path:
        paths.append(Path(env_path))

    # 2. 플랫폼별 기본 경로
    home = Path.home()

    # Windows
    if platform.system() == "Windows":
        paths.extend([
            home / "Desktop",
            home / "바탕화면",
            home / "Documents",
            home / "문서"
        ])
    # macOS
    elif platform.system() == "Darwin":
        paths.extend([
            home / "Desktop",
            home / "Documents",
            home / "Developer"
        ])
    # Linux
    else:
        paths.extend([
            home / "Desktop",
            home / "Documents",
            home / "workspace",
            home / "projects"
        ])

    # 3. 현재 디렉토리
    paths.append(Path.cwd())

    # 중복 제거하고 존재하는 경로만 반환
    valid_paths = []
    seen = set()
    for path in paths:
        if path not in seen and path.exists():
            valid_paths.append(path)
            seen.add(path)

    return valid_paths

@safe_execution
def flow_project_with_workflow(
    project: str,
    *,
    auto_read_docs: bool = True,
    readme_lines: int = 60,
    file_dir_lines: int = 120
) -> Dict[str, Any]:
    """
    프로젝트 전환 & 워크플로우 초기화 + README / file_directory 자동 출력

    이제 os.chdir를 사용하지 않고 Session을 통해 프로젝트를 관리합니다.

    Parameters
    ----------
    project : str
        프로젝트 디렉토리 이름 (바탕화면에서 검색)
    auto_read_docs : bool
        True 이면 README.md 와 file_directory.md 를 자동 출력
    readme_lines / file_dir_lines : int
        각각 출력할 최대 줄 수
    """
    # Import here to avoid circular imports
    from .session import get_current_session
    from .flow_context import ProjectContext, find_project_path

    # 1) 프로젝트 찾기
    project_path = find_project_path(project)

    if not project_path:
        print(f"❌ 프로젝트를 찾을 수 없습니다: {project}")
        print(f"\n💡 팁: PROJECT_BASE_PATH 환경변수를 설정하여 기본 경로를 지정할 수 있습니다.")
        return err(f"프로젝트를 찾을 수 없습니다: {project}")

    # 2) Session을 통해 프로젝트 설정 (os.chdir 없이)
    session = get_current_session()
    previous_project = session.get_project_name()

    try:
        # 프로젝트 설정
        project_ctx = session.set_project(project, str(project_path))
    except Exception as e:
        return err(f"프로젝트 설정 실패: {e}")

    # 캐시 리셋
    global _current_project_cache
    _current_project_cache = None

    # 3) 프로젝트 정보 수집
    proj_info = project_ctx.get_project_info()

    # 캐시 파일 업데이트
    try:
        cache_dir = Path.home() / ".ai-coding-brain" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_data = proj_info.copy()
        cache_data['switched_at'] = datetime.now().isoformat()
        cache_data['previous_project'] = previous_project

        with open(cache_dir / "current_project.json", 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except:
        pass  # 캐시 실패는 무시

    # 4) 기본 정보 출력
    print(f"✅ 프로젝트 전환: {project}")
    print(f"📍 경로: {project_path}")
    print(f"📁 Flow 저장소: {project}/.ai-brain/flow/")
    if previous_project and previous_project != project:
        print(f"   (이전: {previous_project})")

    # 5) 문서 자동 읽기
    docs: Dict[str, str] = {}
    if auto_read_docs:
        # ProjectContext의 read_file 메서드 사용
        readme_txt = project_ctx.read_file("readme.md")
        if readme_txt:
            # 줄 수 제한
            lines = readme_txt.split('\n')[:readme_lines]
            readme_txt = '\n'.join(lines)
            docs["readme.md"] = readme_txt
            print("\n📖 README.md 내용:")
            print("=" * 70)
            print(readme_txt)

        fd_txt = project_ctx.read_file("file_directory.md")
        if fd_txt:
            # 줄 수 제한
            lines = fd_txt.split('\n')[:file_dir_lines]
            fd_txt = '\n'.join(lines)
            docs["file_directory.md"] = fd_txt
            print("\n📁 프로젝트 구조 (file_directory.md):")
            print("=" * 70)
            print(fd_txt)

    # 6) Git 상태 (프로젝트 경로 기준)
    git_info = None
    try:
        # Git 명령어는 아직 cwd 기반이므로 임시로 디렉토리 변경
    # Git 상태 확인 (os.chdir 없이)
    try:
        # subprocess의 cwd 파라미터를 사용하여 프로젝트 디렉토리에서 실행
        import subprocess
        result = subprocess.run(
            ['git', 'status', '--porcelain'], 
            cwd=str(project_path),
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            # Git 저장소인 경우
            files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            clean = len(files) == 0
            
            # 브랜치 정보 가져오기
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(project_path),
                capture_output=True,
                text=True
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            print(f"\n🔀 Git 상태:")
            print("============================================================")
            print(f"브랜치: {branch}")
            print(f"변경 파일: {len(files)}개")
            print(f"상태: {'Clean' if clean else 'Modified'}")
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
    result_data = {
        'project': project,
        'path': str(project_path),
        'info': proj_info,
        'docs': docs,
        'git': git_info,
        'flow': flow_info,
        'switched_from': previous_project
    }

    return ok(result_data)
# 나머지 함수들은 그대로 유지
@safe_execution
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


@safe_execution
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

