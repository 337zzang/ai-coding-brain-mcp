"""
AI Helpers New - Facade Pattern 적용 (안전한 버전)
Phase 2-A 구현
Version: 2.7.0
"""

# 1. Facade 인스턴스 가져오기 (안전한 버전 사용)
from .facade_safe import get_facade
_facade = get_facade()

# 2. 네임스페이스 직접 노출 (새로운 방식)
file = _facade.file
code = _facade.code
search = _facade.search
git = _facade.git
llm = getattr(_facade, 'llm', None)
o3 = getattr(_facade, 'o3', None)
flow = getattr(_facade, 'flow', None)
project = getattr(_facade, 'project', None)

# 3. 주요 함수들 하위 호환성 - 모두 안전하게 가져오기
# 파일 관련
read = getattr(_facade, 'read', None)
write = getattr(_facade, 'write', None)
append = getattr(_facade, 'append', None)
exists = getattr(_facade, 'exists', None)
get_file_info = getattr(_facade, 'get_file_info', None)

# 코드 관련
parse = getattr(_facade, 'parse', None)
replace = getattr(_facade, 'replace', None)
insert = getattr(_facade, 'insert', None)
view = getattr(_facade, 'view', None)
functions = getattr(_facade, 'functions', None)
classes = getattr(_facade, 'classes', None)

# 검색 관련
search_files = getattr(_facade, 'search_files', None)
search_code = getattr(_facade, 'search_code', None)
find_function = getattr(_facade, 'find_function', None)
find_class = getattr(_facade, 'find_class', None)
grep = getattr(_facade, 'grep', None)

# Git 관련
git_status = getattr(_facade, 'git_status', None)
git_commit = getattr(_facade, 'git_commit', None)
git_add = getattr(_facade, 'git_add', None)
git_push = getattr(_facade, 'git_push', None)
git_pull = getattr(_facade, 'git_pull', None)
git_diff = getattr(_facade, 'git_diff', None)
git_log = getattr(_facade, 'git_log', None)
git_branch = getattr(_facade, 'git_branch', None)
git_checkout = getattr(_facade, 'git_checkout', None)
git_checkout_b = getattr(_facade, 'git_checkout_b', None)
git_merge = getattr(_facade, 'git_merge', None)

# LLM/O3 관련
ask_o3 = getattr(_facade, 'ask_o3', None)
ask_o3_async = getattr(_facade, 'ask_o3_async', None)
ask_o3_practical = getattr(_facade, 'ask_o3_practical', None)
check_o3_status = getattr(_facade, 'check_o3_status', None)
get_o3_result = getattr(_facade, 'get_o3_result', None)
show_o3_progress = getattr(_facade, 'show_o3_progress', None)
clear_completed_tasks = getattr(_facade, 'clear_completed_tasks', None)

# Flow 관련
get_flow_api = getattr(_facade, 'get_flow_api', None)
create_task_logger = getattr(_facade, 'create_task_logger', None)

# Project 관련
get_current_project = getattr(_facade, 'get_current_project', None)
flow_project_with_workflow = getattr(_facade, 'flow_project_with_workflow', None)
fp = getattr(_facade, 'fp', flow_project_with_workflow)  # 별칭

# Phase 1에서 추가된 함수들
search_imports = getattr(_facade, 'search_imports', None)
get_statistics = getattr(_facade, 'get_statistics', None)

# 4. 필수 import (다른 모듈에서 필요할 수 있음)
try:
    from .domain.models import Plan, Task, TaskStatus
except ImportError:
    Plan = Task = TaskStatus = None

try:
    from .wrappers import wrap_output
except ImportError:
    wrap_output = None

try:
    from .util import ok, err, is_ok, get_data, get_error
except ImportError:
    ok = err = is_ok = get_data = get_error = None

# 기타 필요한 모듈들 안전하게 import
try:
    from .task_logger import EnhancedTaskLogger, TaskLogger
except ImportError:
    EnhancedTaskLogger = TaskLogger = None

try:
    from .flow_api import FlowAPI
except ImportError:
    FlowAPI = None

# 헬퍼 함수들 - 기존 코드 호환성
def scan_directory(path, max_depth=None):
    """디렉토리 스캔 (하위 호환성)"""
    if file and hasattr(file, 'list_directory'):
        return file.list_directory(path)
    return None

# 버전 정보
__version__ = "2.7.0"
__author__ = "AI Coding Brain Team"

# Public API 정의 (최소)
__all__ = [
    # 네임스페이스 (새로운 방식)
    'file', 'code', 'search', 'git',
    
    # 주요 함수들 (하위 호환성)
    'read', 'write', 'append', 'exists', 'get_file_info',
    'parse', 'replace', 'insert', 'view', 'functions', 'classes',
    'search_files', 'search_code', 'find_function', 'find_class', 'grep',
    'git_status', 'git_commit', 'git_add', 'git_diff', 'git_log',
    'ask_o3', 'ask_o3_async', 'get_o3_result', 'check_o3_status',
    'show_o3_progress', 'clear_completed_tasks',
    'get_flow_api', 'create_task_logger',
    'get_current_project', 'flow_project_with_workflow',
    'search_imports', 'get_statistics',
    
    # 도메인 모델
    'Plan', 'Task', 'TaskStatus',
    
    # 유틸리티
    'ok', 'err', 'is_ok', 'get_data', 'get_error',
    
    # 버전
    '__version__'
]

# 사용법 출력 (선택적)
def help():
    """AI Helpers 사용법 안내"""
    print(_facade)
    print("\n새로운 사용법 (Phase 2-A):")
    print("  import ai_helpers_new as h")
    print("  h.file.read('test.txt')     # 파일 읽기")
    print("  h.code.parse('module.py')   # 코드 분석")
    print("  h.search.files('*.py')      # 파일 검색")
    print("  h.git.status()              # Git 상태")
    print("\n기존 방식도 지원됩니다:")
    print("  h.read('test.txt')          # 레거시 방식")
    if hasattr(_facade, 'stats'):
        return _facade.stats()
    return None

# 초기화 메시지
import warnings
warnings.filterwarnings("default", category=DeprecationWarning)
