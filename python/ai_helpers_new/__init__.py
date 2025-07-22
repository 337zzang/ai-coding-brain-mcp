"""
AI Helpers v2.0 - 통합 헬퍼 모듈
"""

# 기본 imports
from typing import Dict, Any, List, Optional
from datetime import datetime
from .util import ok, err, is_ok, get_data, get_error
from .file import read, write, append, read_json, write_json, exists, info, list_directory
from .code import parse, view, replace, insert, functions, classes
from .search import search_files, search_code, find_function, find_class, grep, find_in_file
from .llm import (
    ask_o3_async, check_o3_status, get_o3_result, 
    save_o3_result,
    show_o3_progress, list_o3_tasks, clear_completed_tasks, prepare_o3_context
)

# Git 함수들
from .git import (
    git_status, git_add, git_commit, git_push, git_pull, 
    git_branch, git_current_branch, git_log, git_diff
)

# Project 함수들  
from .project import (
    get_current_project as _get_current_project_raw,
    detect_project_type,
    scan_directory as _scan_directory_raw,
    scan_directory_dict as _scan_directory_dict_raw,
    create_project_structure,
    fp, flow_project, flow_project_with_workflow
)

# Workflow - 레거시 import 제거
# from .workflow_manager import (
#     WorkflowManager, get_workflow_manager, wf
# )
# from .context_workflow_manager import ContextWorkflowManager, create_context_workflow_manager
# from .flow_command_handler import FlowCommandHandler, get_flow_handler


# Flow Project
# Flow project functions are now in project.py
# 모든 public 함수 export
__all__ = [
    # Util
    'ok', 'err', 'is_ok', 'get_data', 'get_error',

    # File
    'read', 'write', 'append', 'read_json', 'write_json', 'exists', 'info', 'list_directory',

    # Code
    'parse', 'view', 'replace', 'insert', 'functions', 'classes',

    # Search
    'search_files', 'search_code', 'find_function', 'find_class', 'grep', 'find_in_file',

    # LLM
    'ask_o3_async', 'check_o3_status', 'get_o3_result',
    'show_o3_progress', 'list_o3_tasks', 'clear_completed_tasks', 'prepare_o3_context',

    # Git
    'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
    'git_branch', 'git_current_branch', 'git_log', 'git_diff',

    # Project
    'get_current_project', 'detect_project_type',
    'scan_directory', 'scan_directory_dict', 'create_project_structure',

    # Flow Project
    'fp', 'flow_project', 'flow_project_with_workflow',

    # Workflow - FlowManagerUnified만 export
    'FlowManagerUnified', 'WorkflowManager'
]

# 버전 정보
__version__ = "2.0.0"

# 모듈 정보
def help():
    """AI Helpers v2.0 도움말"""
    return """
AI Helpers v2.0 - 주요 함수:

📁 파일 작업:
  - read(path) / write(path, content) / append(path, content)
  - read_json(path) / write_json(path, data)
  - exists(path) / info(path)

📝 코드 분석/수정:
  - parse(path) / view(path, name)
  - replace(path, old, new) / insert(path, marker, code)
  - functions(path) / classes(path)

🔍 검색:
  - search_files(pattern, path) / search_code(pattern, path)
  - find_function(name, path) / find_class(name, path)
  - grep(pattern, path) / find_in_file(file, pattern)

🤖 LLM:
  - ask_o3(question) / ask_o3_async(question)
  - check_o3_status(task_id) / get_o3_result(task_id)
  - show_o3_progress() / list_o3_tasks()

🔀 Git:
  - git_status() / git_add(files) / git_commit(message)
  - git_push() / git_pull() / git_branch(name)
  - git_log(limit) / git_diff(file)

📂 프로젝트:
  - get_current_project() / scan_directory(path)
  - scan_directory_dict(path) / create_project_structure(name)

모든 함수는 {'ok': bool, 'data': Any} 형식의 dict를 반환합니다.
"""


# ========== API 표준화 래핑 (v2.1) ==========
# project.py의 비표준 함수들을 ok/err 패턴으로 표준화
# 원본 함수는 .raw 속성으로 접근 가능 (하위 호환성)

def scan_directory(path: str = '.') -> Dict[str, Any]:
    """디렉토리 스캔 - 표준 응답 패턴"""
    try:
        files = _scan_directory_raw(path)
        return ok(files, count=len(files), path=path)
    except Exception as e:
        return err(f"scan_directory failed: {str(e)}", path=path)

def scan_directory_dict(path: str = '.', max_depth: int = 3) -> Dict[str, Any]:
    """디렉토리 구조를 딕셔너리로 - 표준 응답 패턴"""
    try:
        structure = _scan_directory_dict_raw(path, max_depth)
        return ok(structure, path=path, max_depth=max_depth)
    except Exception as e:
        return err(f"scan_directory_dict failed: {str(e)}", path=path)

def get_current_project() -> Dict[str, Any]:
    """현재 프로젝트 정보 - 표준 응답 패턴"""
    try:
        project_info = _get_current_project_raw()
        return ok(project_info)
    except Exception as e:
        return err(f"get_current_project failed: {str(e)}")

# 원본 함수 노출 (하위 호환성)
scan_directory.raw = _scan_directory_raw
scan_directory_dict.raw = _scan_directory_dict_raw
get_current_project.raw = _get_current_project_raw

print("[AI Helpers v2.1] API standardization completed")

from .context_manager import ContextManager


# Flow Manager Unified
from .flow_manager_unified import FlowManagerUnified
from .flow_proxy import get_workflow_proxy, _workflow_proxy
from .flow_manager_unified import FlowManagerUnified as WorkflowManager  # 호환성

# ========== Workflow Manager Functions (Proxy-based) ==========
def get_workflow_manager(project_root: Optional[str] = None):
    """
    워크플로우 매니저 반환
    project_root가 주어지면 해당 프로젝트로 전환
    """
    proxy = get_workflow_proxy()
    if project_root:
        return proxy.switch(project_root)
    return proxy.current()


def wf(command: str, verbose: bool = False) -> Dict[str, Any]:
    """워크플로우 명령 실행 - 현재 프로젝트의 매니저 사용"""
    try:
        proxy = get_workflow_proxy()

        # 초기화 확인 및 자동 복구 (추가된 부분)
        if proxy._current is None:
            proxy.switch()
            if verbose:
                print("ℹ️ FlowManagerUnified 자동 초기화됨")

        manager = proxy.current()

        if hasattr(manager, 'process_command'):
            result = manager.process_command(command)
            if result.get('ok') and verbose:
                print(f"✅ {result.get('data', '')}")
            elif not result.get('ok') and verbose:
                print(f"❌ {result.get('error', '')}")
            return result
        else:
            return {'ok': False, 'error': 'process_command 메서드가 없습니다'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
# fp 함수 재정의 (프로젝트 전환 시 Flow 매니저도 전환)
def fp(project_name_or_path: str = "", verbose: bool = True) -> Dict[str, Any]:
    """
    프로젝트 전환 (Flow Project)
    프로젝트 전환 시 해당 프로젝트의 Flow 매니저로 자동 전환

    특수 명령:
    - fp("--list"): 바탕화면의 Python 프로젝트 목록
    - fp("--recent"): 최근 사용한 프로젝트 목록
    """
    try:
        import os
        import json
        from pathlib import Path

        # 특수 명령 처리
        if project_name_or_path == "--list":
            desktop = os.path.expanduser("~/Desktop")
            projects = []

            if os.path.exists(desktop):
                for item in os.listdir(desktop):
                    item_path = os.path.join(desktop, item)
                    if os.path.isdir(item_path):
                        # Python 프로젝트 체크
                        if any(f.endswith('.py') for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))):
                            projects.append(item)

            print("📁 사용 가능한 프로젝트:")
            for proj in sorted(projects):
                print(f"  - {proj}")

            return {'success': True, 'data': projects}

        elif project_name_or_path == "--recent":
            recent_file = os.path.join(os.path.expanduser("~"), ".ai-brain-recent.json")
            recent = []

            if os.path.exists(recent_file):
                with open(recent_file, 'r') as f:
                    recent = json.load(f)

            print("📅 최근 사용한 프로젝트:")
            for i, proj in enumerate(recent[:10], 1):
                print(f"  {i}. {os.path.basename(proj)} ({proj})")

            return {'success': True, 'data': recent}

        # 일반 프로젝트 전환
        if project_name_or_path:
            # 절대 경로인 경우
            if os.path.isabs(project_name_or_path):
                target_path = project_name_or_path
            else:
                # 바탕화면에서 프로젝트 찾기
                desktop = os.path.expanduser("~/Desktop")
                target_path = os.path.join(desktop, project_name_or_path)

                # 현재 디렉토리의 상위에서도 찾기
                if not os.path.exists(target_path):
                    parent = os.path.dirname(os.getcwd())
                    alt_path = os.path.join(parent, project_name_or_path)
                    if os.path.exists(alt_path):
                        target_path = alt_path
        else:
            # 빈 문자열이면 현재 디렉토리
            target_path = os.getcwd()

        # 디렉토리 존재 확인
        if not os.path.exists(target_path):
            return {
                'success': False,
                'error': f'프로젝트 디렉토리를 찾을 수 없습니다: {project_name_or_path}'
            }

        # 디렉토리 변경
        old_path = os.getcwd()
        os.chdir(target_path)

        # Flow 매니저 전환
        proxy = get_workflow_proxy()
        proxy.switch(target_path)

        # 최근 프로젝트 기록
        recent_file = os.path.join(os.path.expanduser("~"), ".ai-brain-recent.json")
        recent = []

        if os.path.exists(recent_file):
            with open(recent_file, 'r') as f:
                recent = json.load(f)

        # 현재 프로젝트를 맨 앞에 추가 (중복 제거)
        recent = [target_path] + [r for r in recent if r != target_path][:9]

        with open(recent_file, 'w') as f:
            json.dump(recent, f)

        # 프로젝트 정보 반환
        project_name = os.path.basename(target_path)
        result = {
            'success': True,
            'project': {
                'name': project_name,
                'path': target_path,
                'type': 'python',
                'has_git': os.path.exists(os.path.join(target_path, '.git')),
                'switched_at': datetime.now().isoformat()
            },
            'previous': old_path
        }

        if verbose:
            print(f"✅ 프로젝트 전환: {project_name}")
            print(f"📍 경로: {target_path}")
            print(f"🔄 Flow 매니저도 전환됨")

        return result

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# ============================================================================
# Flow Proxy 자동 초기화
# ============================================================================
def _auto_init_proxy():
    """
    모듈 로드 시 자동으로 현재 프로젝트의 FlowManagerUnified 초기화

    이 함수는 첫 wf() 호출 시 빈 context가 반환되는 문제를 해결합니다.
    프록시가 초기화되지 않은 경우 현재 디렉토리를 기준으로 자동 초기화합니다.
    """
    try:
        # 프록시 가져오기
        proxy = get_workflow_proxy()

        # 초기화되지 않은 경우에만 초기화
        if proxy._current is None:
            # 현재 디렉토리 기준으로 프로젝트 초기화
            proxy.switch()

            # 디버그 모드에서만 로그 출력
            if os.environ.get('DEBUG_FLOW'):
                print("✅ FlowManagerUnified 자동 초기화 완료")
                if proxy._current:
                    print(f"   - 프로젝트: {os.path.basename(proxy._current.project_root)}")
                    print(f"   - Flows: {len(proxy._current.flows)}")

    except Exception as e:
        # 모듈 로드를 방해하지 않도록 조용히 실패
        if os.environ.get('DEBUG_FLOW'):
            print(f"⚠️ Flow 자동 초기화 실패: {e}")
        # 실패해도 모듈 로드는 계속됨
        pass


# 모듈 로드 시 자동 초기화 실행
_auto_init_proxy()
