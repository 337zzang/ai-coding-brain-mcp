"""
Enhanced Flow - 통합 버전
기존 시스템과 호환되도록 수정된 v2
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from project_initializer import create_new_project as _create_new_project
from typing import Dict, Any, Optional
from datetime import datetime

# path_utils에서 필요한 함수들 import
from path_utils import write_gitignore, is_git_available
from python.utils.io_helpers import write_json, atomic_write


# 로깅 설정 - stderr로 출력하여 JSON 응답 오염 방지
# 환경 변수로 디버그 모드 제어
import os
debug_mode = os.environ.get('FLOW_DEBUG', 'false').lower() == 'true'
logging.basicConfig(
    level=logging.DEBUG if debug_mode else logging.WARNING,
    stream=sys.stderr,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# MCP JSON 응답 오염 방지를 위해 print를 logger.info로 리디렉션
import builtins
_original_print = builtins.print
def safe_print(*args, **kwargs):
    """print를 logger.info로 리디렉션"""
    message = ' '.join(str(arg) for arg in args)
    logger.info(message)
# 리디렉션 임시 비활성화 - print 출력 문제 해결을 위해
# builtins.print = safe_print

# helpers 자동 주입 - 모듈 로드 시점에 확인
if not hasattr(builtins, 'helpers'):
    try:
        from helpers_wrapper import HelpersWrapper
        import ai_helpers
        builtins.helpers = HelpersWrapper(ai_helpers)
        logger.info("Enhanced Flow에서 helpers 자동 주입 완료")
    except Exception as e:
        logger.warning(f"helpers 자동 주입 실패: {e}")

# 전역 변수
context = {}
last_loaded_context = None
current_workflow_manager = None  # 현재 프로젝트의 워크플로우 매니저

def get_current_workflow_manager():
    """현재 프로젝트의 워크플로우 매니저 반환"""
    global current_workflow_manager
    
    if current_workflow_manager is None:
        # 워크플로우 매니저가 없으면 현재 프로젝트로 새로 생성
        from python.workflow.improved_manager import ImprovedWorkflowManager
        current_project = Path.cwd().name
        current_workflow_manager = ImprovedWorkflowManager(current_project)
        logger.info(f"[WORKFLOW] 워크플로우 매니저 자동 생성: {current_project}")
    
    return current_workflow_manager


# ==================== 프로젝트 관리 함수 ====================

def cmd_flow_with_context(project_name: str, auto_proceed: bool = False) -> Dict[str, Any]:
    """프로젝트로 전환하고 전체 컨텍스트를 로드

    Args:
        project_name: 프로젝트 이름
        auto_proceed: 자동 진행 여부 (False면 진행 중인 태스크가 있을 때 확인 요청)
    
    기존 인터페이스 유지하면서 개선된 구조 적용
    """
    global context, last_loaded_context

    try:
        # 0. 안전 점검 수행
        logger.info("=" * 60)
        logger.info(f"[START] 프로젝트 전환: {project_name}")
        logger.info("=" * 60)

        safety_check = _safe_project_check(project_name)
        if safety_check is None:
            raise RuntimeError("_safe_project_check() returned None")

        # 오류가 있으면 중단
        if safety_check.get("errors"):
            print("\n[ERROR] 안전 점검 실패:")
            for error in safety_check["errors"]:
                print(f"   - {error}")
            return {
                "success": False,
                "error": "안전 점검 실패",
                "details": safety_check
            }

        # 경고 표시
        if safety_check.get("warnings"):
            print("\n[WARN]  경고 사항:")
            for warning in safety_check["warnings"]:
                print(f"   - {warning}")

            # Git 수정사항이 있으면 확인
            git_info = safety_check["checks"].get("git", {})
            if git_info.get("ok") and git_info.get("modified"):
                print("\n[TIP] 수정된 파일을 백업하시겠습니까? (권장)")
                print("   나중에 'git stash' 또는 'git commit'으로 백업 가능합니다.")

        print("\n[OK] 안전 점검 완료! 프로젝트 전환을 계속합니다...\n")


        # 1. 프로젝트 경로 확인/생성
        project_path = _get_project_path(project_name)

        # 1-1. 프로젝트 존재 여부 확인
        if not project_path.exists():
            error_msg = f"프로젝트 '{project_name}'을 찾을 수 없습니다. 먼저 'start_project'로 생성해주세요."
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'project_name': project_name
            }

        # 2. 이전 컨텍스트와 다른 프로젝트인 경우 로그만 남김
        if context and context.get('project_name') != project_name:
            logger.info(f"프로젝트 전환: {context.get('project_name')} -> {project_name}")
            # context_backup 로직 제거됨 - 더 이상 필요하지 않음

        # 3. 디렉토리 전환
        os.chdir(project_path)
        logger.info(f"[OK] 작업 디렉토리 변경: {project_path}")
        
        # 3-1. memory 폴더 체크 및 정리
        memory_path = project_path / 'memory'
        if not memory_path.exists():
            # memory 폴더가 없으면 생성
            memory_path.mkdir(exist_ok=True)
            logger.info("[OK] memory 폴더 생성")
        else:
            # 기존 memory 폴더가 있는 경우, context.json 확인
            old_context_file = memory_path / 'context.json'
            if old_context_file.exists():
                try:
                    with open(old_context_file, 'r', encoding='utf-8') as f:
                        old_context = json.load(f)
                        old_project = old_context.get('project_name')
                        
                    # 다른 프로젝트의 context인 경우 백업 후 정리
                    if old_project and old_project != project_name:
                        logger.warning(f"[WARN] 다른 프로젝트({old_project})의 memory 발견. 정리 중...")
                        
                        # 기존 context만 백업 (다른 파일들은 그대로 유지)
                        backup_name = f'context_backup_{old_project}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                        backup_path = memory_path / backup_name
                        old_context_file.rename(backup_path)
                        logger.info(f"[OK] 이전 프로젝트 context 백업: {backup_name}")
                        
                except Exception as e:
                    logger.warning(f"기존 context 확인 중 오류: {e}")

        # 4. sys.path 업데이트
        if str(project_path) not in sys.path:
            sys.path.insert(0, str(project_path))

        # 5. 컨텍스트 로드
        context = _load_context(project_name)
        context['project_name'] = project_name
        context['project_path'] = str(project_path)
        context['last_updated'] = datetime.now().isoformat()

        # 6. 컨텍스트 저장
        _save_context(context)

        # 7. 워크플로우 로드 및 표시
        workflow_status = _load_and_show_workflow()
        
        # 7-1. 전역 워크플로우 매니저 재설정
        global current_workflow_manager
        try:
            from python.workflow.improved_manager import ImprovedWorkflowManager
            current_workflow_manager = ImprovedWorkflowManager(project_name)
            logger.info(f"[WORKFLOW] 전역 워크플로우 매니저를 '{project_name}'로 재설정")
        except Exception as e:
            logger.warning(f"[WORKFLOW] 전역 워크플로우 매니저 재설정 실패: {e}")
        
        # 7-2. helpers 객체의 캐시된 워크플로우 매니저 무효화
        try:
            if 'helpers' in globals() and hasattr(helpers, '_workflow_manager'):
                delattr(helpers, '_workflow_manager')
                logger.info("[WORKFLOW] helpers의 캐시된 워크플로우 매니저 제거")
        except Exception as e:
            logger.debug(f"[WORKFLOW] helpers 캐시 제거 중 오류 (무시): {e}")
        
        # 종합 컨텍스트 구축 - 함수가 없으므로 주석 처리
        # comprehensive_ctx = _build_comprehensive_context(project_name, workflow_status)
        

        # 8. Git 상태 확인 및 context에 추가
        git_info = _safe_git_status(os.getcwd())
        if git_info.get("ok"):
            context['git'] = {
                'branch': git_info.get('branch', 'unknown'),
                'modified': git_info.get('modified', []),
                'untracked': git_info.get('untracked', []),
                'untracked_count': git_info.get('untracked_count', 0)
            }

        # 9. 프로젝트 구조 업데이트
        _update_file_directory()

        # 10. 결과 출력
        if workflow_status is None:
            workflow_status = {}
        
        # DEBUG 로그 제거 - 필요시 주석 해제
        # logger.info(f"[DEBUG] 브리핑 함수 호출 전:")
        # logger.info(f"  - project_name: {project_name}")
        # logger.info(f"  - workflow_status type: {type(workflow_status)}")
        # logger.info(f"  - context keys: {list(context.keys()) if context else 'None'}")
        
        # 브리핑 함수 호출 및 반환값 저장
        briefing_result = _print_project_briefing(project_name, workflow_status, context, auto_proceed)
        
        # DEBUG 로그 제거 - 필요시 주석 해제
        # logger.info(f"[DEBUG] 브리핑 함수 반환값:")
        # logger.info(f"  - type: {type(briefing_result)}")
        # logger.info(f"  - value: {briefing_result}")
        
        # 만약 다른 곳에서 briefing_result를 사용한다면 여기서 처리
        # 예: global briefing_cache 등

        last_loaded_context = project_name
# 🔄 기존 프로젝트일 경우 컨텍스트 문서 자동 업데이트
        logger.info("[BUILD] 프로젝트 컨텍스트 문서 업데이트 시작")
        try:
            from python.project_context_builder import ProjectContextBuilder
            builder = ProjectContextBuilder()  # 현재 작업 디렉터리가 프로젝트 루트
            builder.build_all(update_readme=True, update_context=True)
            logger.info("[BUILD] 프로젝트 컨텍스트 문서 업데이트 완료")
        except Exception as e:
            logger.error(f"프로젝트 컨텍스트 문서 업데이트 실패: {e}")
            # 빌드 실패해도 프로젝트 전환은 계속 진행

        # 반환 직전 로깅 추가
        return_data = {
            'success': True,
            'project_name': project_name,
            'context': context if context else {},  # None 방지
            'workflow_status': workflow_status if workflow_status else {}  # None 방지
        }
        
        # Workflow V3 dispatcher 업데이트 - dispatcher 모듈이 없으므로 주석 처리
        # try:
        #     from python.workflow.dispatcher import update_dispatcher_project
        #     update_dispatcher_project(project_name)
        #     logger.info(f"[WORKFLOW] V3 dispatcher를 '{project_name}' 프로젝트로 업데이트")
        # except Exception as e:
        #     logger.warning(f"[WORKFLOW] V3 dispatcher 업데이트 실패: {e}")
        
        # DEBUG 로그 제거 - 필요시 주석 해제
        # logger.info(f"[DEBUG] cmd_flow_with_context 최종 반환값:")
        # logger.info(f"  - success: {return_data['success']}")
        # logger.info(f"  - context type: {type(return_data['context'])}")
        # logger.info(f"  - context is None: {return_data['context'] is None}")
        # logger.info(f"  - context keys: {list(return_data['context'].keys()) if return_data['context'] else 'None/Empty'}")
        
        return return_data

    except Exception as e:
        logger.error(f"프로젝트 전환 실패: {e}")
        return {
            'success': False,
            'project_name': project_name,
            'context': {},  # 빈 dict로 기본값 제공
            'workflow_status': {},  # 빈 dict로 기본값 제공
            'error': str(e)
        }



# ==================== 안전 점검 함수들 ====================

def _safe_git_status(repo_path: str = ".") -> Dict[str, Any]:
    """Git 상태를 안전하게 확인하는 함수"""
    try:
        from git import Repo, InvalidGitRepositoryError
        repo = Repo(repo_path, search_parent_directories=True)
        branch = repo.active_branch.name
        modified = [item.a_path for item in repo.index.diff(None)]
        # untracked = repo.untracked_files  # 성능 문제로 주석 처리
        untracked_count = len(repo.untracked_files) if len(repo.untracked_files) < 1000 else "1000+"  # 성능 최적화
        return {
            "ok": True,
            "branch": branch,
            "modified": modified,
            "untracked_count": untracked_count  # 파일 목록 대신 개수만 반환
        }
    except Exception as e:
        # GitPython 실패 → CLI fallback
        try:
            out = subprocess.check_output(
                ["git", "-C", repo_path, "status", "-sb"],
                text=True,
                stderr=subprocess.STDOUT
            )
            return {"ok": True, "raw": out}
        except Exception as cli_e:
            return {"ok": False, "error": f"{type(cli_e).__name__}: {cli_e}"}


def _safe_load_json(path: Path) -> Dict[str, Any]:
    """JSON 파일을 안전하게 로드하는 함수"""
    try:
        # helpers.read_file 존재 확인
        if 'helpers' in globals():
            helpers = globals()['helpers']
            if hasattr(helpers, 'read_file'):
                data = helpers.read_file(str(path))
                if isinstance(data, str):
                    data = json.loads(data)
                elif isinstance(data, bytes):
                    data = json.loads(data.decode())
                elif isinstance(data, dict):
                    pass  # 이미 파싱되어 있음
                else:
                    raise TypeError("Unknown data type from read_file")
                return {"ok": True, "data": data}

        # 표준 open 사용
        with open(path, encoding="utf-8") as f:
            return {"ok": True, "data": json.load(f)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _print_directory_tree(path: Path, depth: int = 1, max_depth: int = 2):
    """디렉터리 트리를 출력하는 함수"""
    if depth > max_depth:
        return

    try:
        items = list(path.iterdir())
        # 파일과 디렉터리 분리
        dirs = [p for p in items if p.is_dir() and not p.name.startswith('.')]
        files = [p for p in items if p.is_file() and not p.name.startswith('.')]

        # 정렬
        dirs.sort()
        files.sort()

        # 출력 (최대 10개씩)
        for p in (dirs[:5] + files[:5]):
            indent = "│   " * (depth - 1)
            prefix = "└── " if p.is_file() else "[DIR] "
            print(f"{indent}{prefix}{p.name}")

            if p.is_dir() and depth < max_depth:
                _print_directory_tree(p, depth + 1, max_depth)

        if len(dirs) > 5 or len(files) > 5:
            indent = "│   " * (depth - 1)
            print(f"{indent}... ({len(dirs)} 디렉터리, {len(files)} 파일)")

    except PermissionError:
        pass


def _safe_project_check(project_name: str) -> Dict[str, Any]:
    """프로젝트 상태를 안전하게 점검하는 함수"""
    result = {
        "project_name": project_name,
        "checks": {},
        "warnings": [],
        "errors": []
    }

    # 1. 현재 작업 디렉터리 확인
    cwd = Path.cwd()
    result["checks"]["cwd"] = {
        "path": str(cwd),
        "exists": cwd.exists(),
        "is_dir": cwd.is_dir()
    }

    print(f"[SEARCH] 현재 작업 디렉터리: {cwd}")

    # 2. 프로젝트 구조 간단히 확인
    print("\n[DIR] 프로젝트 구조 (최상위 2레벨):")
    _print_directory_tree(cwd, 1, 2)

    # 3. Git 상태 점검
    print("\n[SEARCH] Git 상태 점검 중...")
    git_info = _safe_git_status()
    result["checks"]["git"] = git_info

    if git_info.get("ok"):
        if "branch" in git_info:
            print(f"[OK] Git 브랜치: {git_info['branch']}")
            print(f"   수정된 파일: {len(git_info.get('modified', []))}")
            print(f"   추적되지 않은 파일: {git_info.get('untracked_count', 0)}")

            # 수정된 파일이 있으면 경고
            if git_info.get('modified'):
                result["warnings"].append("수정된 파일이 있습니다. 백업을 권장합니다.")
                print("\n[WARN]  수정된 파일 목록:")
                for f in git_info['modified'][:5]:
                    print(f"   - {f}")
                if len(git_info['modified']) > 5:
                    print(f"   ... 외 {len(git_info['modified']) - 5}개")
        else:
            print("[OK] Git 상태 확인 (raw output)")
    else:
        result["errors"].append(f"Git 상태 확인 실패: {git_info.get('error')}")
        print(f"[ERROR] Git 상태 확인 실패: {git_info.get('error')}")

    # 4. workflow.json 점검
    print("\n[SEARCH] 워크플로우 상태 점검 중...")
    # workflow.json 통일 경로 사용
    wf_paths = [Path("memory/workflow.json")]
    
    wf_path = None
    for path in wf_paths:
        if path.exists():
            wf_path = path
            break

    if wf_path.exists():
        wf_data = _safe_load_json(wf_path)
        result["checks"]["workflow"] = wf_data

        if wf_data.get("ok"):
            data = wf_data["data"]
            plan_id = data.get("current_plan_id")
            plans = {p["id"]: p for p in data.get("plans", [])}
            current = plans.get(plan_id)

            if current:
                tasks = current.get("tasks", [])
                done = sum(1 for t in tasks if t.get("status") == "completed")
                print(f"[OK] 활성 플랜: {current['name']} ({done}/{len(tasks)} 완료)")
            else:
                print("[WARN]  활성 플랜이 없습니다.")
        else:
            result["warnings"].append(f"workflow.json 로드 실패: {wf_data.get('error')}")
            print(f"[WARN]  workflow.json 로드 실패: {wf_data.get('error')}")
    else:
        print("[WARN]  workflow.json 파일이 없습니다.")
        result["warnings"].append("workflow.json 파일이 없습니다.")

    # 5. helpers 모듈 상태 확인
    print("\n[SEARCH] helpers 모듈 상태 확인 중...")
    helpers_ok = False

    try:
        # helpers를 여러 위치에서 확인
        helpers = None
        if hasattr(builtins, 'helpers'):
            helpers = builtins.helpers
        elif 'helpers' in globals():
            helpers = globals()['helpers']
        elif 'helpers' in locals():
            helpers = locals()['helpers']

        if helpers:
            # 주요 메서드 확인
            required_methods = ['read_file', 'create_file', 'git_status']
            missing = [m for m in required_methods if not hasattr(helpers, m)]

            if not missing:
                print("[OK] helpers 모듈 정상")
                helpers_ok = True
            else:
                result["warnings"].append(f"helpers 메서드 누락: {missing}")
                print(f"[WARN]  helpers 메서드 누락: {missing}")
        else:
            result["warnings"].append("helpers 모듈을 찾을 수 없습니다.")
            print("[WARN]  helpers 모듈을 찾을 수 없습니다.")
    except Exception as e:
        result["errors"].append(f"helpers 확인 중 오류: {e}")
        print(f"[ERROR] helpers 확인 중 오류: {e}")

    result["checks"]["helpers_ok"] = helpers_ok

    return result

# ===========================================================

def _get_project_path(project_name: str) -> Path:
    """프로젝트 경로 가져오기 - OS 독립적 Desktop 경로 사용

    우선순위:
    1. FLOW_PROJECT_ROOT 환경변수
    2. AI_PROJECTS_DIR 환경변수
    3. 사용자 Desktop 폴더 (OS 독립적)
    """
    # 환경변수 확인
    base_path = os.environ.get('FLOW_PROJECT_ROOT')
    if not base_path:
        base_path = os.environ.get('AI_PROJECTS_DIR')

    # 환경변수가 없으면 Desktop 사용
    if not base_path:
        # OS 독립적인 Desktop 경로 찾기
        desktop_path = Path.home() / "Desktop"

        # Desktop 폴더가 없는 경우 (일부 Linux 환경)
        if not desktop_path.exists():
            # XDG_DESKTOP_DIR 환경변수 확인 (Linux)
            xdg_desktop = os.environ.get('XDG_DESKTOP_DIR')
            if xdg_desktop and Path(xdg_desktop).exists():
                desktop_path = Path(xdg_desktop)
            else:
                # 대체 경로들 시도
                alt_paths = [
                    Path.home() / "바탕화면",  # 한글 Windows
                    Path.home() / "桌面",      # 중국어
                    Path.home() / "デスクトップ"  # 일본어
                ]
                for alt in alt_paths:
                    if alt.exists():
                        desktop_path = alt
                        break
                else:
                    # 모두 실패하면 홈 디렉토리 사용
                    desktop_path = Path.home() / "Projects"
                    desktop_path.mkdir(exist_ok=True)

        base_path = str(desktop_path)

    project_path = Path(base_path) / project_name

    # 프로젝트 경로만 반환 (자동 생성하지 않음)
    return project_path

def _load_context(project_name: str) -> Dict[str, Any]:
    """컨텍스트 로드 - 프로젝트별 독립적 로드"""
    context_file = Path('memory') / 'context.json'

    if context_file.exists():
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                loaded_context = json.load(f)
                
                # 중요: 로드된 context의 project_name이 현재 프로젝트와 일치하는지 확인
                if loaded_context.get('project_name') == project_name:
                    return loaded_context
                else:
                    # 다른 프로젝트의 context인 경우 새로 생성
                    logger.warning(f"기존 context가 다른 프로젝트({loaded_context.get('project_name')})의 것임. 새 context 생성.")
                    
        except Exception as e:
            logger.warning(f"컨텍스트 로드 실패: {e}")

    # 기본 컨텍스트 생성
    return {
        'project_name': project_name,
        'created_at': datetime.now().isoformat(),
        'description': f'{project_name} 프로젝트',
        'version': '1.0.0',
        'last_modified': datetime.now().isoformat()
    }

def _save_context(ctx: Dict[str, Any]):
    """컨텍스트 저장"""
    context_file = Path('memory') / 'context.json'

    try:
        os.makedirs('memory', exist_ok=True)
        # write_json 사용 (data, path 순서)
        write_json(ctx, context_file)
        logger.info("[OK] 컨텍스트 저장 완료")
    except Exception as e:
        logger.error(f"컨텍스트 저장 실패: {e}")

def ensure_workflow_file(project_path: Path = None) -> Path:
    """프로젝트에 워크플로우 파일이 있는지 확인하고 없으면 생성"""
    if project_path is None:
        project_path = Path.cwd()
    
    workflow_dir = project_path / 'memory' / 'active'
    workflow_file = workflow_dir / 'workflow.json'
    
    # 디렉토리 생성
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    # 워크플로우 파일이 없으면 생성
    if not workflow_file.exists():
        project_name = project_path.name
        
        # 기본 워크플로우 구조
        default_workflow = {
            'version': '3.0',
            'active_project': project_name,
            'projects': {
                project_name: {
                    'current_plan': None,
                    'events': [],
                    'version': '3.0.0',
                    'metadata': {
                        'created_at': datetime.now().isoformat(),
                        'last_updated': datetime.now().isoformat()
                    }
                }
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        }
        
        # 중앙 워크플로우에서 기존 데이터 확인 (마이그레이션)
        try:
            central_path = Path.home() / 'Desktop' / 'ai-coding-brain-mcp' / 'memory' / 'active' / 'workflow.json'
            if central_path.exists() and central_path != workflow_file:
                with open(central_path, 'r', encoding='utf-8') as f:
                    central_data = json.load(f)
                
                # 해당 프로젝트 데이터가 있으면 마이그레이션
                if project_name in central_data.get('projects', {}):
                    project_data = central_data['projects'][project_name]
                    default_workflow['projects'][project_name] = project_data
                    logger.info(f"중앙 워크플로우에서 {project_name} 데이터 마이그레이션 완료")
        except Exception as e:
            logger.warning(f"중앙 워크플로우 마이그레이션 실패: {e}")
        
        # 파일 저장
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(default_workflow, f, indent=2, ensure_ascii=False)
        
        logger.info(f"워크플로우 파일 생성: {workflow_file}")
    
    return workflow_file


def _load_and_show_workflow() -> Dict[str, Any]:
    """워크플로우 로드 및 상태 반환 - ImprovedWorkflowManager 사용"""
    global current_workflow_manager
    try:
        # ImprovedWorkflowManager 사용
        from python.workflow.improved_manager import ImprovedWorkflowManager
        
        # 현재 프로젝트명
        current_project = Path.cwd().name
        
        # ImprovedWorkflowManager 인스턴스 생성
        wm = ImprovedWorkflowManager(current_project)
        current_workflow_manager = wm  # 전역 변수에 저장
        logger.info(f"[WORKFLOW] ImprovedWorkflowManager 인스턴스 로드: {current_project}")
        
        # 상태 확인
        status_result = wm.get_status()
        
        # status가 'no_plan'이 아닌 경우에만 성공으로 처리
        if status_result and status_result.get('status') != 'no_plan':
            workflow_status = status_result
            logger.info(f"[WORKFLOW] 워크플로우 상태 로드 성공: {workflow_status.get('status')}")
            return workflow_status
        else:
            logger.info("[WORKFLOW] 활성 워크플로우 없음")
            return {'status': 'no_plan', 'message': '활성 계획 없음'}
        
    except Exception as e:
        logger.error(f"워크플로우 로드 중 오류: {e}")
        # 오류 발생 시 파일에서 직접 읽기 시도
        try:
            workflow_file = Path("memory/workflow.json")
            if workflow_file.exists():
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 활성 플랜 찾기
                if data.get('plans') and data.get('active_plan_id'):
                    for plan in data['plans']:
                        if plan['id'] == data['active_plan_id']:
                            tasks = plan.get('tasks', [])
                            completed = sum(1 for t in tasks if t.get('status') == 'completed')
                            current_task = None
                            
                            # 현재 태스크 찾기
                            for task in tasks:
                                if task.get('status') in ['todo', 'in_progress']:
                                    current_task = task
                                    break
                            
                            return {
                                'status': 'active',
                                'plan_id': plan['id'],
                                'plan_name': plan.get('name', '이름 없음'),
                                'plan_description': plan.get('description', ''),
                                'total_tasks': len(tasks),
                                'completed_tasks': completed,
                                'progress': (completed / len(tasks) * 100) if tasks else 0,
                                'current_task': current_task
                            }
        except Exception as e2:
            logger.error(f"파일 직접 읽기도 실패: {e2}")
        
        return {'status': 'error', 'message': f'워크플로우 로드 실패: {str(e)}'}

def _update_file_directory():
    """파일 디렉토리 업데이트 - helpers 의존성 제거"""
    try:
        import os
        import glob
        from pathlib import Path

        # 현재 디렉토리 정보 수집
        current_dir = Path('.')
        files = []
        directories = []

        # 파일과 디렉토리 수집 (최대 깊이 3)
        for item in current_dir.rglob('*'):
            if len(item.parts) > 4:  # 깊이 제한
                continue
            if item.is_file():
                files.append(str(item))
            elif item.is_dir():
                directories.append(str(item))

        # file_directory.md 생성
        content = f"# File Directory\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 파일 목록
        content += "## Files\n"
        for file in sorted(files)[:100]:  # 최대 100개 파일
            content += f"- {file}\n"
        if len(files) > 100:
            content += f"... and {len(files) - 100} more files\n"

        # 디렉토리 목록
        content += "\n## Directories\n"
        for dir in sorted(directories)[:50]:  # 최대 50개 디렉토리
            content += f"- {dir}/\n"
        if len(directories) > 50:
            content += f"... and {len(directories) - 50} more directories\n"

        # 파일 쓰기 - atomic_write 사용 (data, path 순서)
        from pathlib import Path
        atomic_write(content, Path('file_directory.md'))

        logger.info("[OK] file_directory.md 업데이트 완료")

    except Exception as e:
        logger.warning(f"파일 디렉토리 업데이트 실패: {e}")

def _show_recent_events(project_name: str, limit: int = 5):
    """최근 워크플로우 이벤트 표시"""
    try:
        events_file = Path("memory/workflow_events.json")
        if events_file.exists():
            with open(events_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            events = data.get('events', [])
            if events:
                print(f"\n📋 최근 워크플로우 이벤트 (최근 {limit}개):")
                for event in events[-limit:]:
                    timestamp = event.get('timestamp', 'N/A')
                    event_type = event.get('type', 'unknown')
                    entity_id = event.get('entity_id', 'N/A')
                    
                    # 이벤트 타입에 따른 아이콘
                    icon = {
                        'state_changed': '🔄',
                        'task_completed': '✅',
                        'task_started': '▶️',
                        'error_occurred': '❌',
                        'plan_created': '📝',
                        'task_added': '➕'
                    }.get(event_type, '•')
                    
                    # 시간 포맷팅
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = timestamp
                    
                    print(f"   {icon} [{time_str}] {event_type}")
                    
                    # state_changed의 경우 상세 정보 표시
                    if event_type == 'state_changed' and 'data' in event:
                        from_state = event['data'].get('from', 'N/A')
                        to_state = event['data'].get('to', 'N/A')
                        print(f"      {from_state} → {to_state}")
    except Exception as e:
        logger.debug(f"이벤트 표시 중 오류: {e}")


def _print_project_briefing(project_name: str, workflow_status: Dict[str, Any], context: Dict[str, Any], auto_proceed: bool = False):
    """프로젝트 브리핑 출력 - 개선된 버전"""
    print("\n" + "=" * 50)
    print(f"[START] 프로젝트 전환: {project_name}")
    print("=" * 50)
    print(f"[OK] 작업 디렉토리: {os.getcwd()}")

    # Git 상태 확인
    try:
        # _safe_git_status 함수 직접 호출
        git_info = _safe_git_status(os.getcwd())
        if git_info.get("ok"):
            # Git 정보를 context에 저장
            context['git'] = {
                'branch': git_info.get('branch', 'unknown'),
                'modified': git_info.get('modified', []),
                'untracked': git_info.get('untracked', []),
                'untracked_count': git_info.get('untracked_count', 0)
            }

            print(f"\n[GIT] Git 브랜치: {git_info.get('branch', 'N/A')}")
            modified_count = len(git_info.get('modified', []))
            print(f"[EDIT] 변경된 파일: {modified_count}개")

            if git_info.get('modified'):
                print("\n변경된 파일:")
                modified_files = git_info.get('modified', [])
                for file in modified_files[:5]:  # 최대 5개
                    print(f"  - {file}")
                if modified_count > 5:
                    print(f"  ... 외 {modified_count - 5}개")
    except Exception as e:
        # Git 상태 실패 시 조용히 넘어감
        pass

    # 워크플로우 상태
    print("\n" + "=" * 50)
    if workflow_status and workflow_status.get('status') == 'active':
        print(f"[LIST] 워크플로우: {workflow_status.get('plan_name') if workflow_status else 'None'}")
        print(f"[STAT] 진행률: {workflow_status.get('completed_tasks') if workflow_status else 0}/{workflow_status.get('total_tasks') if workflow_status else 0} 완료 ({workflow_status.get('progress', 0):.0f}%)")

        if workflow_status and workflow_status.get('current_task'):
            task = workflow_status.get('current_task', {})
            task_status = task.get('status', 'unknown')
            
            # 태스크 상태에 따른 표시
            if task_status == 'in_progress' and not auto_proceed:
                print(f"🔄 진행 중: {task.get('title')}")
                print("\n⚠️  주의: 현재 진행 중인 태스크가 있습니다!")
                print("   계속하려면 다음 중 하나를 선택하세요:")
                print("   - /continue : 현재 태스크 계속 진행")
                print("   - /complete : 현재 태스크 완료 처리")
                print("   - /pause : 태스크 일시 중지")
                print("   - /status : 상세 상태 확인")
                
                # 최근 이벤트 표시
                _show_recent_events(project_name, 3)
                
            elif task_status == 'in_progress' and auto_proceed:
                print(f"🔄 진행 중: {task.get('title')}")
                print("[AUTO] 자동 진행 모드 - 태스크 계속 진행")
                
            else:
                print(f"▶️  다음 작업: {task.get('title')}")
                print("[TIP] /next로 작업 시작")
                
        # 진행 중인 태스크가 있고 자동 진행이 비활성화되어 있으면 자동 진행 방지 메시지
        if not auto_proceed and any(t.get('status') == 'in_progress' for t in workflow_status.get('tasks', [])):
            print("\n💡 자동 진행 방지 모드가 활성화되었습니다.")
            print("   작업을 진행하려면 명시적으로 명령을 입력하세요.")
    else:
        print("[LIST] 워크플로우: 활성 계획 없음")
        print("[TIP] /plan 명령으로 새 계획 생성")

    print("=" * 50)
    print("[OK] 프로젝트 전환 완료!")
    print("=" * 50)
    
    # 브리핑 정보를 반환하여 재사용 가능하도록 함
    return_value = {
        "project_path": os.getcwd(),
        "git": context.get("git", {}),
        "workflow_status": workflow_status,
    }
    
    # DEBUG 로그 제거 - 필요시 주석 해제
    # logger.info(f"[DEBUG] _print_project_briefing 반환값:")
    # logger.info(f"  - type: {type(return_value)}")
    # logger.info(f"  - keys: {list(return_value.keys())}")
    # logger.info(f"  - project_path: {return_value.get('project_path')}")
    
    return return_value

def show_workflow_status_improved() -> Dict[str, Any]:
    """개선된 워크플로우 상태 표시"""
    workflow_status = _load_and_show_workflow()

    print("\n" + "━" * 50)
    if workflow_status and workflow_status.get('status') == 'active':
        print(f"[LIST] 워크플로우: {workflow_status.get('plan_name') if workflow_status else 'None'}")
        print(f"[STAT] 진행률: {workflow_status.get('completed_tasks') if workflow_status else 0}/{workflow_status.get('total_tasks') if workflow_status else 0} 완료")
        print("━" * 50)

        if workflow_status and workflow_status.get('current_task'):
            task = workflow_status.get('current_task', {})
            print(f"▶️  현재 작업: {task.get('title')}")
            print(f"   상태: {task.get('status', 'pending')}")
            print(f"   설명: {task.get('description', 'N/A')}")
            print("\n[TIP] /next 명령으로 다음 작업 진행")
    else:
        print("[LIST] 현재 활성 계획이 없습니다.")
        print("[TIP] /plan 명령으로 새 계획을 생성하세요.")
    print("━" * 50)

    # workflow_status가 None인 경우 기본값 반환
    return workflow_status or {'status': 'no_workflow', 'message': '워크플로우 없음'} or {'status': 'no_workflow', 'message': '워크플로우 없음'}

# 헬퍼 바인딩용 함수


def start_project(project_name: str, init_git: bool = True) -> Dict[str, Any]:
    """새 프로젝트 생성

    Args:
        project_name: 생성할 프로젝트 이름
        init_git: Git 초기화 여부 (기본값: True)

    Returns:
        Dict[str, Any]: 생성 결과
            - success: 성공 여부
            - project_name: 프로젝트 이름
            - project_path: 프로젝트 경로
            - created: 생성된 항목들
            - message: 결과 메시지
            - error: 오류 메시지 (실패 시)
    """
    try:
        logger.info(f"새 프로젝트 생성 시작: {project_name}")

        # project_initializer 모듈 사용
        from python.project_initializer import create_new_project
        result = create_new_project(project_name, init_git=init_git)

        if result.ok:
            data = result.data
            logger.info(f"프로젝트 생성 성공: {project_name}")

            # 성공 결과 반환
            return {
                'success': True,
                'project_name': data.get('project_name'),
                'project_path': data.get('project_path'),
                'created': data.get('created', {}),
                'message': data.get('message', f"프로젝트 '{project_name}' 생성 완료")
            }
        else:
            logger.error(f"프로젝트 생성 실패: {result.error}")
            return {
                'success': False,
                'error': result.error,
                'project_name': project_name
            }

    except Exception as e:
        logger.error(f"프로젝트 생성 중 예외 발생: {e}")
        return {
            'success': False,
            'error': f"프로젝트 생성 중 오류 발생: {str(e)}",
            'project_name': project_name
        }

def flow_project(project_name: str, auto_proceed: bool = False):
    """helpers.flow_project() 래퍼"""
    return cmd_flow_with_context(project_name, auto_proceed)

# helpers 바인딩 함수
def bind_to_helpers(helpers_obj):
    """helpers 객체에 함수 바인딩"""
    helpers_obj.flow_project = flow_project
    helpers_obj.cmd_flow_with_context = cmd_flow_with_context
    helpers_obj.start_project = start_project
    helpers_obj.show_workflow_status = show_workflow_status_improved
    logger.info("Enhanced Flow 함수들이 helpers에 바인딩되었습니다")

# 모듈 로드 시 자동 실행
if __name__ != "__main__":
    # helpers가 있으면 자동 바인딩
    try:
        import sys
        if 'helpers' in sys.modules:
            helpers_module = sys.modules['helpers']
            # AIHelpers 또는 HelpersWrapper 모두 지원
            if hasattr(helpers_module, 'AIHelpers') or hasattr(helpers_module, 'helpers'):
                try:
                    # 전역 helpers 객체가 있는지 확인
                    import builtins
                    if hasattr(builtins, 'helpers'):
                        bind_to_helpers(builtins.helpers)
                        logger.info("helpers 객체에 enhanced_flow 함수 바인딩 완료")
                except Exception as e:
                    logger.warning(f"helpers 바인딩 실패: {e}")
    except:
        pass
