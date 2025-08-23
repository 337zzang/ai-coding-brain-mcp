"""
프로젝트 관리 및 전환 기능
리팩토링: 2025-08-02
"""
import os
import platform
import json
from typing import Dict, Any, List, Optional
# from .project_context import get_project_context, resolve_project_path  # 리팩토링 후 제거
from datetime import datetime
from pathlib import Path
from .util import ok, err
from .wrappers import safe_execution, safe_api_get
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
    from .session import get_current_session, set_current_project
    
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
    session_ctx = session.project_context
    if not session_ctx:
        return err("프로젝트가 설정되지 않았습니다")
    
    # ProjectContext 인스턴스 생성
    from .flow_context import ProjectContext
    if isinstance(session_ctx, dict) and session_ctx.get('path'):
        project_ctx = ProjectContext(session_ctx['path'])
    else:
        return err("프로젝트 컨텍스트 정보가 유효하지 않습니다")

    # 캐시 확인
    project_path = str(project_ctx.base_path)
    if _current_project_cache and _current_project_cache.get('path') == project_path:
        return ok(_current_project_cache)

    try:
        # 프로젝트 정보 수집
        project_info = project_ctx.to_dict()  # get_project_info 대신 to_dict 사용

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
    claude_lines: int = 100,
    readme_lines: int = 60
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
        session.set_project(project, project_path)
        # ProjectContext 인스턴스 생성
        project_ctx = ProjectContext(project_path)
    except Exception as e:
        return err(f"프로젝트 설정 실패: {e}")

    # 캐시 리셋
    global _current_project_cache
    _current_project_cache = None

    # 3) 프로젝트 정보 수집
    proj_info = project_ctx.to_dict()  # get_project_info 대신 to_dict 사용()

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

    # 5) 문서 자동 읽기 - CLAUDE.md 우선
    docs: Dict[str, str] = {}
    if auto_read_docs:
        from pathlib import Path
        
        # CLAUDE.md 파일 확인 (Claude Code 통합)
        claude_path = Path(project_path) / "CLAUDE.md"
        claude_found = False
        
        if claude_path.exists():
            try:
                with open(claude_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:claude_lines]
                    claude_txt = ''.join(lines)
                    docs["CLAUDE.md"] = claude_txt
                    print("\n🤖 CLAUDE.md 내용 (Claude Code 통합):")
                    print("=" * 70)
                    print(claude_txt)
                    claude_found = True
            except Exception as e:
                print(f"⚠️ CLAUDE.md 읽기 실패: {e}")
        
        # CLAUDE.md가 없거나 실패한 경우 README.md 폴백
        if not claude_found:
            readme_txt = project_ctx.get_readme(readme_lines)
            if readme_txt:
                docs["readme.md"] = readme_txt
                print("\n📖 README.md 내용:")
                print("=" * 70)
                print(readme_txt)

        # 5.5) 최신 플랜 표시 (v75.0)
    try:
        from .flow_api import FlowAPI
        flow_api = FlowAPI()

        # 최신 플랜 3개 가져오기
        plans_result = flow_api.list_plans(limit=3)
        if plans_result['ok'] and plans_result['data']:
            plans = plans_result['data']
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
    # 🛡️ Git 상태 확인 (6단계 안전장치 적용)
    try:
        git_info = None
        git_result = {'ok': False, 'error': 'Git 상태 확인 실패', 'data': {}}

        # 🏁 1단계: Git 저장소 존재 확인
        if not os.path.exists('.git'):
            print("⚠️ Git 저장소(.git)가 없습니다 - 건너뛰기")
            git_result = {'ok': False, 'error': 'No git repository', 'data': {}}
        else:
            # 📦 2단계: 안전한 모듈 Import
            try:
                import ai_helpers_new as helpers
                print("✅ Helpers import 성공")

                # 🔍 3단계: 함수 검증 (hasattr + None + callable)
                if (hasattr(helpers, 'git') and 
                    hasattr(helpers.git, 'status') and 
                    helpers.git.status is not None and 
                    callable(helpers.git.status)):

                    print("✅ git.status 함수 검증 완료")

                    # 🛡️ 4단계: 안전한 호출 (try-except로 실제 호출 보호)
                    try:
                        git_result = helpers.git.status()
                        print("✅ git.status 호출 성공")

                        # 📊 5단계: 반환값 검증 (타입 및 구조 확인)
                        if git_result is None:
                            print("⚠️ git.status가 None 반환")
                            git_result = {'ok': False, 'error': 'git.status returned None', 'data': {}}
                        elif not isinstance(git_result, dict):
                            print(f"⚠️ git.status가 예상치 못한 타입 반환: {type(git_result)}")
                            git_result = {'ok': False, 'error': f'Invalid return type: {type(git_result)}', 'data': {}}
                        elif 'ok' not in git_result:
                            print("⚠️ git.status 반환값에 'ok' 키 없음")
                            git_result = {'ok': False, 'error': 'Missing ok field', 'data': git_result}
                        else:
                            print(f"✅ git.status 반환값 검증 완료: ok={git_result.get('ok', False)}")

                    except Exception as call_error:
                        print(f"❌ git.status 호출 중 오류: {call_error}")
                        git_result = {'ok': False, 'error': f'git.status call failed: {str(call_error)}', 'data': {}}

                else:
                    # 함수가 없거나 호출 불가능한 경우
                    missing_reasons = []
                    if not hasattr(helpers, 'git'):
                        missing_reasons.append("git 네임스페이스 없음")
                    elif not hasattr(helpers.git, 'status'):
                        missing_reasons.append("status 함수 없음")
                    elif helpers.git.status is None:
                        missing_reasons.append("함수가 None")
                    elif not callable(helpers.git.status):
                        missing_reasons.append("호출 불가능")

                    print(f"⚠️ git.status 함수 검증 실패: {', '.join(missing_reasons)}")
                    git_result = {'ok': False, 'error': f'git.status validation failed: {missing_reasons}', 'data': {}}

            except ImportError as import_error:
                print(f"❌ Helpers import 실패: {import_error}")
                git_result = {'ok': False, 'error': f'Import failed: {str(import_error)}', 'data': {}}
            except Exception as module_error:
                print(f"❌ 모듈 관련 오류: {module_error}")
                git_result = {'ok': False, 'error': f'Module error: {str(module_error)}', 'data': {}}

        # Git 상태 정보 처리 (성공한 경우)
        if git_result.get('ok', False) and isinstance(git_result.get('data'), dict):
            git_data = git_result['data']
            files = git_data.get('files', [])
            branch = git_data.get('branch', 'unknown')
            clean = git_data.get('clean', False)

            git_info = {
                'branch': branch,
                'files': files,
                'count': len(files) if isinstance(files, list) else 0,
                'clean': clean
            }

            print(f"\n🔀 Git 상태:")
            print("============================================================")
            print(f"브랜치: {branch}")
            print(f"변경 파일: {git_info['count']}개")
            print(f"상태: {'Clean' if clean else 'Modified'}")
        else:
            print(f"\n⚠️ Git 상태 확인 실패:")
            print("============================================================")
            print(f"오류: {git_result.get('error', 'Unknown error')}")

    except Exception as e:
        # 📝 6단계: 상세 로깅 (모든 단계별 오류 정보 제공)
        print(f"\n❌ Git 섹션 전체 오류:")
        print("============================================================")
        print(f"오류 타입: {type(e).__name__}")
        print(f"오류 메시지: {str(e)}")
        print(f"오류 위치: Git 상태 확인 섹션")
        git_result = {'ok': False, 'error': f'Git section failed: {str(e)}', 'data': {}}
        # Git 상태 실패는 전체 함수 실패로 이어지지 않도록
        print(f"\n⚠️ Git 상태 오류: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
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
    # plan_count 추가 (v3.0 호환성)
    plan_count = 0
    try:
        from .flow_api import FlowAPI
        flow_api = FlowAPI()
        plans_result = flow_api.list_plans()
        if plans_result['ok'] and plans_result['data']:
            plan_count = len(plans_result['data'])
    except:
        pass
    
    result_data = {
        'project': project,
        'path': str(project_path),
        'info': proj_info,
        'docs': docs,
        'git': git_info,
        'flow': flow_info,
        'switched_from': previous_project,
        'plan_count': plan_count  # 추가
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


# ============================================
# ProjectContext 클래스 (project_context.py에서 이동)
# ============================================

class ProjectContext:
    """프로젝트 경로를 관리하는 Context 클래스

    os.chdir을 사용하지 않고 프로젝트별 경로를 관리합니다.
    """

    def __init__(self):
        self._current_project: Optional[str] = None
        self._project_path: Optional[Path] = None
        self._base_path: Optional[Path] = None
        self._initialize_base_path()

    def _initialize_base_path(self):
        """기본 프로젝트 경로 초기화"""
        # 환경변수 우선
        env_path = os.environ.get("PROJECT_BASE_PATH")
        if env_path:
            self._base_path = Path(env_path)
        else:
            # 기본값: 홈/Desktop
            self._base_path = Path.home() / "Desktop"

    def set_project(self, project_name: str) -> None:
        """현재 프로젝트 설정"""
        self._current_project = project_name
        self._project_path = self._base_path / project_name

    def get_project_name(self) -> Optional[str]:
        """현재 프로젝트 이름 반환"""
        return self._current_project

    def get_project_path(self) -> Optional[Path]:
        """현재 프로젝트 경로 반환"""
        return self._project_path

    def resolve_path(self, relative_path: str) -> Path:
        """상대 경로를 프로젝트 기준 절대 경로로 변환"""
        if self._project_path:
            return self._project_path / relative_path
        else:
            # 프로젝트가 설정되지 않은 경우 현재 디렉토리 기준
            return Path.cwd() / relative_path

    def get_base_path(self) -> Path:
        """기본 프로젝트 경로 반환"""
        return self._base_path

    def set_base_path(self, path: str) -> None:
        """기본 프로젝트 경로 설정"""
        self._base_path = Path(path)


# 전역 ProjectContext 인스턴스
_project_context = ProjectContext()


def get_project_context() -> ProjectContext:
    """ProjectContext 싱글톤 인스턴스 반환"""
    return _project_context


def resolve_project_path(relative_path: str) -> str:
    """편의 함수: 상대 경로를 프로젝트 기준 절대 경로로 변환"""
    return str(get_project_context().resolve_path(relative_path))



# ============= 유저 프리퍼런스 v3.0 누락 함수 추가 =============
# 2025-08-09: 테스트에서 발견된 누락 함수들 구현

def select_plan_and_show(plan_id_or_number: str):
    """플랜 선택 및 상세 정보 표시 (JSONL 로그 포함)

    Args:
        plan_id_or_number: 플랜 ID 또는 번호

    Returns:
        dict: {'ok': bool, 'data': dict, 'error': str}
    """
    try:
        from .flow_api import FlowAPI
        import os
        import json

        api = FlowAPI()

        # 플랜 선택
        select_result = api.select_plan(plan_id_or_number)
        if not select_result['ok']:
            return select_result

        plan_id = safe_api_get(select_result, 'data.id')
        if plan_id is None:
            return {'ok': False, 'error': 'Failed to get plan ID from selection'}

        # 플랜 정보 가져오기
        plan_info = api.get_plan(plan_id)
        if not plan_info['ok']:
            return plan_info

        # Task 목록 가져오기
        tasks = api.list_tasks(plan_id)
        if not tasks['ok']:
            return tasks

        # JSONL 로그 파일 읽기
        flow_dir = get_project_context().resolve_path(".ai-brain/flow")
        plan_dir = flow_dir / "plans" / plan_id

        logs = []
        if plan_dir.exists():
            for task_file in sorted(plan_dir.glob("*.jsonl")):
                with open(task_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            logs.append(json.loads(line))

        return {
            'ok': True,
            'data': {
                'plan': plan_info['data'],
                'tasks': tasks['data'],
                'logs': logs,
                'log_count': len(logs)
            }
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fix_task_numbers(plan_id: str):
    """Task number가 None인 경우 자동 복구

    Args:
        plan_id: 플랜 ID

    Returns:
        dict: {'ok': bool, 'data': dict, 'error': str}
    """
    try:
        from .flow_api import FlowAPI

        api = FlowAPI()

        # Task 목록 가져오기
        tasks_result = api.list_tasks(plan_id)
        if not tasks_result['ok']:
            return tasks_result

        tasks = tasks_result['data']
        fixed_count = 0

        # Task number 복구
        for i, task in enumerate(tasks, 1):
            if task.get('number') is None:
                # Task 업데이트
                update_result = api.update_task(
                    plan_id, 
                    task['id'],
                    number=i
                )
                if update_result['ok']:
                    fixed_count += 1

        return {
            'ok': True,
            'data': {
                'fixed_count': fixed_count,
                'total_tasks': len(tasks),
                'message': f"Fixed {fixed_count} task numbers"
            }
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def flow_project(project_name: str):
    """단순 프로젝트 전환 (워크플로우 없이)

    Args:
        project_name: 프로젝트 이름

    Returns:
        dict: {'ok': bool, 'data': dict, 'error': str}
    """
    try:
        # Import 필요한 모듈들
        from .session import get_current_session
        from .flow_context import find_project_path
        
        # 프로젝트 경로 찾기
        project_path = find_project_path(project_name)
        if not project_path:
            return {'ok': False, 'error': f"Project '{project_name}' not found"}
        
        # 세션을 통해 프로젝트 설정
        session = get_current_session()
        try:
            session.set_project(project_name, project_path)
        except Exception as e:
            return {'ok': False, 'error': f"Failed to set project: {str(e)}"}

        return {
            'ok': True,
            'data': {
                'project': project_name,
                'path': str(project_path),
                'type': 'project',
                'switched': True
            }
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def project_info():
    """현재 프로젝트 상세 정보

    Returns:
        dict: {'ok': bool, 'data': dict, 'error': str}
    """
    try:
        # 현재 프로젝트 정보
        current = get_current_project()
        if not current['ok']:
            return current

        project_data = current['data']
        project_name = project_data['name']

        # 추가 정보 수집
        project_path = Path(project_data['path'])

        # 파일 통계
        py_files = list(project_path.glob("**/*.py"))
        js_files = list(project_path.glob("**/*.js"))
        ts_files = list(project_path.glob("**/*.ts"))
        md_files = list(project_path.glob("**/*.md"))

        # Git 정보
        git_dir = project_path / ".git"
        has_git = git_dir.exists()

        # Flow 정보
        flow_dir = project_path / ".ai-brain" / "flow"
        has_flow = flow_dir.exists()

        return {
            'ok': True,
            'data': {
                'name': project_name,
                'path': str(project_path),
                'type': project_data.get('type', 'unknown'),
                'has_git': has_git,
                'has_flow': has_flow,
                'statistics': {
                    'python_files': len(py_files),
                    'javascript_files': len(js_files),
                    'typescript_files': len(ts_files),
                    'markdown_files': len(md_files),
                    'total_files': len(py_files) + len(js_files) + len(ts_files) + len(md_files)
                }
            }
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def list_projects():
    """모든 프로젝트 목록

    Returns:
        dict: {'ok': bool, 'data': list, 'error': str}
    """
    try:
        import os

        # 프로젝트 베이스 디렉토리
        base_dir = Path(os.path.expanduser("~/Desktop"))
        if not base_dir.exists():
            base_dir = Path.cwd().parent

        projects = []

        # 프로젝트 폴더 스캔
        for item in base_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 프로젝트 타입 판별
                project_type = None
                if (item / "package.json").exists():
                    project_type = "node"
                elif (item / "pyproject.toml").exists() or (item / "setup.py").exists():
                    project_type = "python"
                elif (item / ".git").exists():
                    project_type = "git"

                if project_type:
                    projects.append({
                        'name': item.name,
                        'path': str(item),
                        'type': project_type,
                        'has_flow': (item / ".ai-brain" / "flow").exists()
                    })

        # 이름순 정렬
        projects.sort(key=lambda x: x['name'])

        return {
            'ok': True,
            'data': projects
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}