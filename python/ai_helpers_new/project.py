"""
프로젝트 관리 및 전환 기능
리팩토링: 2025-08-02
"""
import os
import platform
import json
from typing import Dict, Any, List, Optional
from .project_context import get_project_context, resolve_project_path
from datetime import datetime
from pathlib import Path
from .util import ok, err
from .wrappers import safe_execution
from .core.fs import scan_directory as core_scan_directory, ScanOptions


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

    # cache 변수가 최초 호출 때 정의돼 있지 않으면 초기화
    if '_current_project_cache' not in globals():
        _current_project_cache = None

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

    # 이제 os.chdir를 사용하지 않고 Session을 통해 프로젝트를 관리합니다.

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

    # # 2) Session을 통해 프로젝트 설정 (os.chdir 없이)
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

        # 5.5) 최신 플랜 표시 (v75.0)
    try:
        from .flow_api import FlowAPI
        flow_api = FlowAPI()

        # 최신 플랜 3개 가져오기
        plans_result = flow_api.list_plans(limit=3)
        if plans_result['ok'] and plans_result['data']:
            plans = plans_result['data']
            plans_data = plans  # result_data에 포함시킬 플랜 데이터
            print(f"\n📋 최신 플랜 {len(plans)}개:")
            print("=" * 60)

            for i, plan in enumerate(plans, 1):
                # 플랜은 dict 형태로 반환됨
                print(f"\n{i}. {plan['name']}")
                print(f"   ID: {plan['id']}")
                print(f"   생성일: {plan['created_at']}")
                print(f"   상태: {plan.get('status', 'active')}")

                # Task 상태 분석
                tasks = plan.get('tasks', {})
                if tasks:
                    task_statuses = {}
                    for task_id, task in tasks.items():
                        # Task도 dict 형태
                        status = task.get('status', 'todo')
                        # TaskStatus enum 값 처리
                        if hasattr(status, 'value'):
                            status = str(status)
                        task_statuses[status] = task_statuses.get(status, 0) + 1

                    print(f"   Tasks: {len(tasks)}개", end="")
                    if task_statuses:
                        status_str = ", ".join([f"{status}: {count}" for status, count in task_statuses.items()])
                        print(f" ({status_str})")
                    else:
                        print()
                else:
                    print("   Tasks: 0개")
        elif plans_result['ok']:
            print("\n📋 생성된 플랜이 없습니다.")
    except Exception as e:
        # 플랜 표시 실패는 전체 함수 실패로 이어지지 않도록
        print(f"\n⚠️ 플랜 표시 중 오류 발생: {type(e).__name__}: {e}")
        pass

    print("\n✅ 플랜 섹션 완료, Git 섹션으로 이동...")

                # 6) Git 상태 (프로젝트 경로 기준)
    print("\n🔍 Git 섹션 시작...")
    git_info = None
    try:
        # git_status는 이미 ai_helpers_new에서 사용 가능
        import ai_helpers_new as helpers
        print("Helpers import 성공")
        git_result = helpers.git_status()
        print(f"Git status 결과: {git_result['ok']}")

        if git_result['ok']:
            git_data = git_result['data']
            files = git_data.get('files', [])
            branch = git_data.get('branch', 'unknown')
            clean = git_data.get('clean', False)

            git_info = {
                'branch': branch,
                'files': files,
                'count': len(files),
                'clean': clean
            }

            print(f"\n🔀 Git 상태:")
            print("============================================================")
            print(f"브랜치: {branch}")
            print(f"변경 파일: {len(files)}개")
            print(f"상태: {'Clean' if clean else 'Modified'}")
    except Exception as e:
        # Git 상태 실패는 전체 함수 실패로 이어지지 않도록
        print(f"\n⚠️ Git 상태 오류: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        pass


    # 플랜 데이터 초기화 (2025-08-07)
    plans_data = None
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
        'project_name': project,  # 일관성을 위해 추가
        'path': str(project_path),
        'info': proj_info,
        'docs': docs,
        'git': git_info,
'flow': flow_info,
'plans': plans_data if 'plans_data' in locals() else None,  # 플랜 정보 추가 (2025-08-07)
'switched_from': previous_project
    }

    # 2025-08-07 개선: os.chdir 실행 및 호환성 키 추가
    import os
    
    # 디렉토리 변경 (기본적으로 수행)
    try:
        project_path = result_data.get("path")
        if project_path:
            os.chdir(project_path)
            result_data["current_dir"] = os.getcwd()
            result_data["cwd"] = os.getcwd()
    except Exception as e:
        print(f"⚠️ 디렉토리 변경 실패: {e}")
    
    # Git 호환성 키 추가
    if result_data.get("git") and "count" in result_data["git"]:
        result_data["git"]["changes"] = result_data["git"]["count"]
    
    # Flow 정보가 없으면 추가 시도
    if not result_data.get("flow"):
        try:
            # 동적 import로 순환 참조 방지
            from .flow_api import FlowAPI
            from .ultra_simple_flow_manager import UltraSimpleFlowManager
            
            flow_home = Path(project_path) / ".ai-brain" / "flow" if project_path else None
            if flow_home and flow_home.exists():
                manager = UltraSimpleFlowManager(
                    storage_path=flow_home,
                    project_name=result_data.get("project", "")
                )
                api = FlowAPI(manager)
                plans_result = api.list_plans(limit=3)
                if plans_result.get("ok"):
                    result_data["flow"] = {
                        "recent_plans": plans_result.get("data", []),
                        "count": len(plans_result.get("data", []))
                    }
        except Exception as e:
            # Flow 로드 실패는 무시 (선택적 기능)
            pass
    
    # 버전 정보 추가
    result_data["_version"] = "1.1.0"
    result_data["_modified"] = "2025-08-07"
    
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



def select_plan_and_show(plan_selector):
    """플랜을 선택하고 상세 정보를 표시 (간소화 버전)

    Args:
        plan_selector: 플랜 번호(1,2,3...) 또는 플랜 ID

    Returns:
        dict: 표준 응답 형식
    """
    try:
        from .flow_api import get_flow_api
        import os
        import json

        api = get_flow_api()

        # 플랜 목록 가져오기
        plans_result = api.list_plans(limit=10)
        if not plans_result['ok']:
            return {'ok': False, 'error': 'Failed to get plans'}

        plans = plans_result['data']

        # 선택자가 숫자인 경우
        if isinstance(plan_selector, (int, str)) and str(plan_selector).isdigit():
            idx = int(plan_selector) - 1
            if 0 <= idx < len(plans):
                selected_plan = plans[idx]
            else:
                return {'ok': False, 'error': f'Invalid plan number: {plan_selector}'}
        else:
            # ID로 찾기
            selected_plan = None
            for plan in plans:
                if plan['id'] == plan_selector:
                    selected_plan = plan
                    break

            if not selected_plan:
                return {'ok': False, 'error': f'Plan not found: {plan_selector}'}

        # 플랜 상세 정보 출력
        print(f"\n📋 플랜: {selected_plan['name']}")
        print(f"ID: {selected_plan['id']}")
        print(f"생성: {selected_plan['created_at']}")
        print(f"상태: {selected_plan['status']}")

        # Tasks 정보
        if 'tasks' in selected_plan and selected_plan['tasks']:
            print(f"\n📝 Tasks ({len(selected_plan['tasks'])}개):")
            for task_id, task in selected_plan['tasks'].items():
                number = task.get('number', '?')
                title = task.get('title', 'No title')
                status = task.get('status', 'N/A')
                print(f"  #{number}: {title} [{status}]")

        # JSONL 로그 표시
        print("\n📊 Task 로그:")
        plan_dir = f".ai-brain/flow/plans/{selected_plan['id']}"

        if os.path.exists(plan_dir):
            jsonl_files = [f for f in os.listdir(plan_dir) if f.endswith('.jsonl')]

            for jsonl_file in sorted(jsonl_files):
                print(f"\n📄 {jsonl_file}:")
                file_path = os.path.join(plan_dir, jsonl_file)

                # 파일 크기와 라인 수 확인
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        print(f"  총 {len(lines)}개 이벤트")

                        # 처음과 마지막 이벤트 표시
                        if lines:
                            first_event = json.loads(lines[0])
                            print(f"  시작: {first_event.get('timestamp', 'N/A')}")
                            print(f"  첫 이벤트: {first_event.get('event_type', first_event.get('type', 'N/A'))}")

                            if len(lines) > 1:
                                last_event = json.loads(lines[-1])
                                print(f"  마지막 이벤트: {last_event.get('event_type', last_event.get('type', 'N/A'))}")
                except Exception as e:
                    print(f"  읽기 오류: {e}")

        return {'ok': True, 'data': selected_plan}

    except Exception as e:
        return {'ok': False, 'error': str(e)}

# 원본 함수 백업 (재귀 방지)
import copy
_original_flow_project_with_workflow = None

def setup_safe_wrapper():
    """안전한 wrapper 설정"""
    global _original_flow_project_with_workflow, flow_project_with_workflow

    # 원본 함수가 아직 백업되지 않은 경우에만 백업
    if _original_flow_project_with_workflow is None:
        # 현재 flow_project_with_workflow가 wrapper가 아닌 경우에만
        if flow_project_with_workflow.__name__ != 'flow_project_with_workflow_safe':
            _original_flow_project_with_workflow = flow_project_with_workflow

            def flow_project_with_workflow_safe(
                project: str,
                *,
                auto_read_docs: bool = True,
                readme_lines: int = 60,
                file_dir_lines: int = 120
            ) -> Dict[str, Any]:
                """
                flow_project_with_workflow의 안전한 wrapper
                항상 표준 응답 형식을 보장합니다.
                """
                try:
                    # 원본 함수 호출 (재귀 방지)
                    result = _original_flow_project_with_workflow(
                        project,
                        auto_read_docs=auto_read_docs,
                        readme_lines=readme_lines,
                        file_dir_lines=file_dir_lines
                    )

                    # 반환값 타입 확인 및 표준화
                    if isinstance(result, dict) and 'ok' in result:
                        return result
                    elif isinstance(result, str):
                        return {'ok': False, 'error': f'Unexpected string: {result[:100]}', 'data': None}
                    elif result is None:
                        return {'ok': False, 'error': 'Function returned None', 'data': None}
                    else:
                        return {'ok': True, 'data': result}

                except Exception as e:
                    return {'ok': False, 'error': f'Exception: {e}', 'data': None}

            # 함수 교체
            flow_project_with_workflow = flow_project_with_workflow_safe
            return flow_project_with_workflow

# wrapper 설정 실행
setup_safe_wrapper()
