"""
AI Helpers - 통합 헬퍼 모듈 v14.0 (Simplified)
단순화되고 명확한 import 구조
"""
import logging
import sys
import os
from typing import Dict, Any, List, Optional
from .workflow.workflow_integration import WorkflowIntegration, workflow_integration
from .workflow_integrated_helpers import WorkflowIntegratedHelpers

# from .workflow_aware_helpers import WorkflowAwareHelpers, workflow_helpers # 임시 비활성화
from .usage_guide import show_helper_guide, HELPER_USAGE_GUIDE


# 로깅 설정
logger = logging.getLogger("ai_helpers")
# INFO 레벨로 유지하여 에러는 항상 출력되도록 함
logger.setLevel(logging.INFO)

# stderr 핸들러 추가 - 에러 메시지가 제대로 출력되도록
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

# Helper Result - 가장 먼저 import
from .helper_result import HelperResult

# 워크플로우 통합 헬퍼 시스템
# 기존 helpers를 워크플로우 인식 버전으로 확장
try:
    # 원본 helpers 백업
    _original_helpers = helpers
    # 워크플로우 통합 버전으로 교체
    helpers = WorkflowIntegratedHelpers(_original_helpers)
except Exception as e:
    print(f"⚠️ 워크플로우 통합 실패: {e}")
    # 실패 시 원본 유지

# helpers = workflow_helpers  # WorkflowAwareHelpers 인스턴스 # 임시 비활성화

# 워크플로우 상태 표시 함수
def show_workflow_status():
    """현재 워크플로우 상태를 표시합니다."""
    workflow_helpers.show_workflow_status()

# 헬퍼 사용법 가이드
def show_usage(category=None, function=None):
    """
    헬퍼 함수 사용법을 표시합니다.

    사용법:
    - show_usage(): 전체 카테고리 표시
    - show_usage('파일 작업'): 카테고리별 함수 표시
    - show_usage(function='read_file'): 특정 함수 사용법
    """
    show_helper_guide(category, function)

# 자주 사용하는 헬퍼 함수들을 최상위로 노출
read_file = helpers.read_file
create_file = helpers.create_file
write_file = helpers.write_file
search_files = helpers.search_files
git_status = helpers.git_status
update_task_status = helpers.update_task_status

# 컨텍스트 매니저
workflow_task = helpers.with_workflow_task


# File 관련 - 통합 모듈에서 import
from .file_unified import (
    read_file, write_file, create_file, append_to_file,
    delete_file, copy_file, move_file, file_exists,
    get_file_info, read_lines, read_json, write_json,
    read_yaml, write_yaml
)

# Git 관련 - 통합 모듈에서 import
from .git_enhanced import (
    git_status, git_add, git_commit, git_push, git_pull,
    git_branch, git_log, git_diff, git_stash, git_stash_pop,
    git_commit_smart, is_git_repository, git_init,
    git_checkout, git_get_current_branch, git_get_remote_url,
    GIT_AVAILABLE
)

# Search 관련 - 통합 모듈에서 import
from .search_optimized import (
    search_files,
    search_code,
    find_symbol,
    scan_directory,
    find_class,
    find_function,
    find_import,
    grep,
    # 별칭 (하위 호환성)
    search_files as search_files_advanced,
    search_code as search_code_content
)

# 기존 모듈에서 필요한 것만 import (점진적 마이그레이션)
from .directory_scan import (
    scan_directory_dict,
    cache_project_structure,
    get_project_structure,
    search_in_structure
)

# Legacy aliases for backward compatibility
_search_files_advanced = search_files
_search_code_content = search_code
list_file_paths = lambda directory, pattern="*", recursive=True: [
    f['path'] for f in search_files(directory, pattern, recursive=recursive, include_details=True).data.get('results', [])
]
grep_code = grep
scan_dir = scan_directory

# Optional 모듈들 - try/except로 처리
# Compile 관련
try:
    from .compile import (
        check_syntax, compile_project,
        replace_block, insert_block, get_snippet_preview
    )
except ImportError as e:
    # logger.warning(f"⚠️ compile 모듈 로드 실패: {e}")
    pass

# Build 관련
try:
    from .build import build_project
except ImportError as e:
    # logger.warning(f"⚠️ build 모듈 로드 실패: {e}")
    pass

# Code 관련 - 통합 모듈에서 import
try:
    # from .code_unified import (  # Removed - use code.py instead
    #     parse_code, replace_function, replace_class, replace_method,
    #     add_function, add_method_to_class, get_code_snippet,
    #     find_code_element, set_verbose as set_code_verbose
    # )
    # Legacy compatibility
    from .code import (
        replace_block, insert_block, parse_with_snippets
    )
except ImportError as e:
    logger.warning(f"⚠️ code 모듈 로드 실패: {e}")

# Project/Context 관련 - 통합 모듈에서 import
try:
    from .project_unified import (
        get_current_project, create_project, list_projects,
        quick_task, list_tasks, complete_task, get_project_progress,
        create_standard_phases, get_current_phase, get_pending_tasks,
        # Context management (legacy)
        get_context, update_context, save_context, initialize_context
    )
except ImportError as e:
    logger.warning(f"⚠️ project_unified 모듈 로드 실패: {e}")

# Decorators functionality moved to utility_unified.py

# Utils functionality moved to utility_unified.py and project_unified.py


# Utility 관련 - 통합 모듈에서 import
from .utility_unified import (
    track_operation, lazy_import, list_functions, safe_import,
    get_tracking_statistics, reset_tracking,
    # Legacy aliases
    track_file_access, get_project_context
)

# Legacy replacements
try:
    from .legacy_replacements import (
        cmd_flow, list_tasks,
        get_pending_tasks, get_work_tracking_summary, get_event_history,
        run_command, get_flow_instance, edit_block, update_symbol_index,
        get_verbose, set_verbose
    )
except ImportError as e:
    # logger.warning(f"⚠️ legacy_replacements 모듈 로드 실패: {e}")
    pass

# API 관련
try:
    from .api import toggle_api, list_apis, check_api_enabled
except ImportError as e:
    logger.warning(f"⚠️ api 모듈 로드 실패: {e}")

# Workflow 함수 정의
def workflow(command: str):
    """워크플로우 명령어 실행"""
    try:
        # python.workflow 패키지 경로 추가 (v47 수정)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # ImprovedWorkflowManager 사용 (개선된 버전)
        from python.workflow.improved_manager import ImprovedWorkflowManager
        
        # 현재 프로젝트명 가져오기
        current_project = os.path.basename(os.getcwd())
        wm = ImprovedWorkflowManager(current_project)
        
        # 명령 처리
        result = wm.process_command(command)
        
        # 결과 출력 (무응답 문제 해결)
        if isinstance(result, dict):
            if result.get('message'):
                print(result['message'])
            elif result.get('output'):
                print(result['output'])
        elif isinstance(result, str):
            print(result)
        
        # HelperResult로 변환
        if isinstance(result, dict) and result.get('success'):
            return HelperResult(True, data=result)
        else:
            error_msg = result.get('message', 'Unknown error') if isinstance(result, dict) else str(result)
            return HelperResult(False, error=error_msg)
            
    except Exception as e:
        print(f"❌ 워크플로우 오류: {e}")
        return HelperResult(False, error=str(e))

# Flow 관련 함수들
def flow_project(project_name: str):
    """
    통합된 flow_project 함수
    프로젝트 전환과 워크플로우 상태를 동기화합니다.
    """
    return workflow_integration.flow_project(project_name)

def start_project(project_name: str, init_git: bool = True) -> Dict[str, Any]:
    """새 프로젝트 생성"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            
        from enhanced_flow import start_project as _start_project_func
        result = _start_project_func(project_name, init_git)
        return result
    except Exception as e:
        logger.error(f"start_project 실행 실패: {e}")
        return {'success': False, 'error': f"프로젝트 생성 실패: {str(e)}"}

# 모듈 로드 상태 추적
_load_status = {
    'core': True,  # helper_result, file, git, search는 필수
    'optional': {}  # 선택적 모듈들의 로드 상태
}

def get_load_status() -> Dict[str, Any]:
    """모듈 로드 상태 반환"""
    return _load_status

# __all__ 정의 - 명시적으로 export할 항목들
__all__ = [
    # Core
    'HelperResult',
    
    # File operations
    'read_file', 'write_file', 'create_file', 'append_to_file',
    'delete_file', 'copy_file', 'move_file', 'file_exists',
    'get_file_info', 'read_lines', 'read_json', 'write_json',
    'read_yaml', 'write_yaml',
    'scan_directory', 'scan_directory_dict',
    
    # Git operations
    'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
    'git_branch', 'git_log', 'git_diff', 'git_stash', 'git_stash_pop',
    'git_commit_smart',  'is_git_repository', 'git_init',
    'git_checkout', 'git_get_current_branch', 'git_get_remote_url',
    'GIT_AVAILABLE',
    
    # Search operations
    'search_files', 'search_code', 'find_symbol', 'scan_directory',
    'find_class', 'find_function', 'find_import', 'grep',
    # Legacy aliases
    'search_files_advanced', '_search_files_advanced',
    'search_code_content', '_search_code_content',
    'cache_project_structure', 'get_project_structure', 'search_in_structure',
    'scan_directory_dict', 'list_file_paths', 'grep_code', 'scan_dir',
    
    # Workflow
    'workflow', 'flow_project', 'start_project', 'get_current_project',
    'create_project', 'list_projects',
    
        # Utilities
    'get_load_status',

    # Utility Operations (새로 통합된 기능들)
    'track_operation', 'lazy_import', 'list_functions', 'safe_import',
    'get_tracking_statistics', 'reset_tracking',
    # Legacy aliases
    'track_file_access', 'get_project_context',
]

# Optional 모듈의 함수들도 __all__에 추가 (존재하는 경우에만)
optional_exports = [
    # Compile
    'check_syntax', 'compile_project', 'parse_with_snippets',
    'replace_block', 'insert_block',
    # Code operations
    'parse_code', 'replace_function', 'replace_class', 'replace_method',
    'add_function', 'add_method_to_class', 'get_code_snippet',
    'find_code_element', 'set_code_verbose',
    
    # Build
    'build_project',
    
    # Code
    'ASTParser', 'EnhancedFunctionReplacer', 'FunctionReplacer',
    'ClassReplacer', 'BlockInsertTransformer',
    
    # Context
    'get_context', 'save_context', 'update_context', 'initialize_context',
    'get_project_context', 'track_file_operation', 'track_function_edit',
    'track_operation',
    
    # Project
    'detect_project_type', 'install_dependencies', 'get_project_progress',
    'get_system_summary',
    
    # Utils
    'get_current_phase', 'complete_current_phase', 'create_standard_phases',
    'quick_task', 'task', 'complete', 'progress', 'reset_project',
    'update_cache', 'get_cache_value', 'track_file_access', 'get_value',
    'safe_print',
    
    # Legacy
    'cmd_flow', 'get_current_project', 'list_functions', 'list_tasks',
    'get_pending_tasks', 'get_work_tracking_summary', 'get_event_history',
    'run_command', 'get_flow_instance', 'edit_block', 'update_symbol_index',
    'get_verbose', 'set_verbose',
    
    # API
    'toggle_api', 'list_apis', 'check_api_enabled',
]

# 실제로 로드된 함수만 __all__에 추가
for name in optional_exports:
    if name in globals():
        __all__.append(name)

logger.info(f"AI Helpers 초기화 완료 - {len(__all__)}개 함수 export")

# Web Automation module
try:
    # 웹 자동화 레코딩 함수들 추가
    from python.api.web_automation_helpers import (
        web_automation_record_start,
        web_automation_record_stop,
        web_automation_record_status,
        web_record_demo
    )
    WEB_AUTOMATION_AVAILABLE = True
    
    # __all__에 추가
    __all__.extend([
        'open_browser', 'navigate_to', 'search_google', 
        'take_screenshot', 'close_browser', 'demo_google_search',
        'web_automation_record_start', 'web_automation_record_stop',
        'web_automation_record_status', 'web_record_demo'
    ])
    
except ImportError as e:
    # print(f"Web automation 모듈 로드 실패: {e}")
    WEB_AUTOMATION_AVAILABLE = False


# REPL 호환 브라우저 자동화 메서드 추가
try:
    from python.api.web_automation_repl import REPLBrowser
    _browser = REPLBrowser()
    
    # 메서드 바인딩
    browser = _browser
    browser_start = _browser.start
    browser_goto = _browser.goto
    browser_click = _browser.click
    browser_type = _browser.type
    browser_screenshot = _browser.screenshot
    browser_wait = _browser.wait
    browser_eval = _browser.eval
    browser_get_content = _browser.get_content
    browser_stop = _browser.stop
    
    # __all__에 추가
    __all__.extend([
        'browser', 'browser_start', 'browser_goto', 'browser_click',
        'browser_type', 'browser_screenshot', 'browser_wait', 
        'browser_eval', 'browser_get_content', 'browser_stop'
    ])
    
    print("✅ REPL 브라우저 자동화 메서드 로드 완료")
    
except ImportError as e:
    print(f"REPL 브라우저 모듈 로드 실패: {e}")


# LLM 헬퍼 함수 추가
try:
    from python.ai_helpers.llm_helper import (
        ask_llm,
        ask_code_review,
        ask_design_help,
        ask_error_help,
        ask_optimize_code
    )
    
    # __all__에 추가
    __all__.extend([
        'ask_llm', 'ask_code_review', 'ask_design_help',
        'ask_error_help', 'ask_optimize_code'
    ])
    
    print("✅ LLM 헬퍼 함수 로드 완료 (o3 모델 지원)")
    
except ImportError as e:
    print(f"LLM 헬퍼 모듈 로드 실패: {e}")


# 워크플로우 통합 함수들
from .workflow_helper import workflow as _workflow_helper

def show_workflow_status():
    """현재 워크플로우 상태 표시"""
    _workflow_helper.show_status()

def update_task_status(status, note=None):
    """현재 태스크 상태 업데이트"""
    return _workflow_helper.update_task_status(status, note)

def get_current_task():
    """현재 진행 중인 태스크 가져오기"""
    return _workflow_helper.get_current_task()

def get_current_workflow():
    """현재 워크플로우 상태 가져오기"""
    return _workflow_helper.get_current_workflow()

# helpers 객체에 워크플로우 메서드 추가 (있는 경우)
if 'helpers' in locals():
    try:
        import types
        helpers.show_workflow_status = show_workflow_status
        helpers.update_task_status = update_task_status
        helpers.get_current_task = get_current_task
        helpers.get_current_workflow = get_current_workflow
        helpers.workflow = _workflow_helper
    except:
        pass
