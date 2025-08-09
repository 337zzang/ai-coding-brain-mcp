"""
AI Helpers New - Facade Pattern 적용
Phase 2-A 구현 완료
Version: 2.7.0
"""

# 1. Facade 인스턴스 가져오기 (최소 버전 사용)
from .facade_minimal import get_facade
_facade = get_facade()

# 2. 네임스페이스 직접 노출 (새로운 방식)
file = _facade.file
code = _facade.code
search = _facade.search
git = _facade.git
llm = _facade.llm
o3 = _facade.o3
flow = _facade.flow
project = _facade.project

# 3. 기존 flat API 하위 호환성 (deprecated)
# 파일 관련
read = _facade.read
write = _facade.write
append = _facade.append
exists = _facade.exists
get_file_info = _facade.get_file_info
create_directory = _facade.create_directory
move_file = getattr(_facade, 'move_file', None)  # 선택적
scan_directory = _facade.scan_directory
read_multiple_files = getattr(_facade, 'read_multiple_files', None)  # 선택적

# 코드 관련
parse = _facade.parse
view = _facade.view
replace = _facade.replace
insert = _facade.insert
functions = _facade.functions
classes = _facade.classes
delete = _facade.code.delete  # 직접 참조

# 검색 관련
search_files = _facade.search_files
search_code = _facade.search_code
find_function = _facade.find_function
find_class = _facade.find_class
grep = _facade.grep
search_imports = getattr(_facade, 'search_imports', None)
get_statistics = getattr(_facade, 'get_statistics', None)

# Git 관련
git_status = _facade.git_status
git_add = _facade.git_add
git_commit = _facade.git_commit
git_diff = _facade.git_diff
git_log = _facade.git_log
git_branch = _facade.git_branch
git_checkout = _facade.git_checkout
git_checkout_b = _facade.git_checkout_b
git_merge = _facade.git_merge
git_push = _facade.git_push
git_pull = _facade.git_pull
git_stash = _facade.git_stash
git_reset_hard = _facade.git_reset_hard
git_current_branch = _facade.git_current_branch
git_status_normalized = _facade.git_status_normalized

# LLM/O3 관련
ask_o3 = _facade.ask_o3
ask_o3_async = _facade.ask_o3_async
ask_o3_practical = getattr(_facade.llm, 'ask_o3_practical', ask_o3)
check_o3_status = _facade.check_o3_status
get_o3_result = _facade.get_o3_result
show_o3_progress = _facade.show_o3_progress
clear_completed_tasks = _facade.clear_completed_tasks
O3ContextBuilder = getattr(_facade.llm, 'ContextBuilder', None)

# Flow 관련
get_flow_api = _facade.get_flow_api
create_task_logger = _facade.create_task_logger
flow_project_with_workflow = _facade.flow_project_with_workflow
select_plan_and_show = _facade.select_plan_and_show
wf = _facade.wf
FlowAPI = _facade.flow.API
EnhancedTaskLogger = _facade.flow.TaskLogger

# Project 관련
get_current_project = _facade.get_current_project
safe_get_current_project = _facade.safe_get_current_project
fp = _facade.fp
get_project_context = _facade.get_project_context
resolve_project_path = _facade.resolve_project_path

# 4. 도메인 모델과 타입 (그대로 유지)
from .domain.models import Plan, Task, TaskStatus
from .ultra_simple_flow_manager import UltraSimpleFlowManager

# 5. 추가로 필요한 나머지 함수들 (평면 구조 유지)
# 이 부분은 점진적으로 네임스페이스로 이동 예정
from .task_logger import display_plan_tasks
from .simple_flow_commands import flow as flow_cmd
from .flow_views import format_task, format_plan_with_tasks
from .flow_helpers import FlowHelpers, get_simplified_plan
from .flow_manager_utils import create_minimal_flow_manager
from .contextual_flow_manager import contextual_flow_manager
from .context_integration import ContextIntegration
from .context_reporter import ContextReporter

# Wrappers
from .wrappers import wrap_output

# Utils
from .util import ok, err, is_ok, get_data, get_error

# Backup utils
from .backup_utils import create_backup, restore_backup, list_backups

# Excel Manager (선택적)
try:
    from .excel_manager import ExcelManager
    excel_manager = ExcelManager()
except ImportError:
    excel_manager = None

# 기타 헬퍼 함수들
from .file import find_in_file
from .code import log_code_change
from .git import (
    git_branch_d,
    git_pull_origin,
    git_push_origin,
    git_rebase,
    git_reset_soft,
    git_status_short,
    git_tag
)

# 타입 힌트용
from typing import Any, Dict, List, Optional, Union

# 버전 정보
__version__ = "2.7.0"
__author__ = "AI Coding Brain Team"

# Public API 정의
__all__ = [
    # 네임스페이스 (새로운 방식)
    'file', 'code', 'search', 'git', 'llm', 'o3', 'flow', 'project',

    # 주요 함수들 (하위 호환성)
    'read', 'write', 'append', 'exists',
    'parse', 'view', 'replace', 'insert',
    'search_files', 'search_code', 'find_function', 'find_class',
    'git_status', 'git_commit', 'git_push', 'git_pull',
    'ask_o3', 'ask_o3_async', 'get_o3_result',
    'get_flow_api', 'create_task_logger',
    'get_current_project', 'fp', 'wf',

    # 도메인 모델
    'Plan', 'Task', 'TaskStatus',

    # 타입과 유틸리티
    'ok', 'err', 'is_ok', 'get_data', 'get_error',
    'wrap_output',

    # 버전
    '__version__'
]

# 사용법 출력 (선택적)
def help():
    """AI Helpers 사용법 안내"""
    print(_facade)
    print("\n새로운 사용법:")
    print("  import ai_helpers_new as h")
    print("  h.file.read('test.txt')  # 파일 읽기")
    print("  h.code.parse('module.py')  # 코드 분석")
    print("  h.git.status()  # Git 상태")
    print("\n기존 방식도 지원됩니다 (deprecated):")
    print("  h.read('test.txt')  # DeprecationWarning 발생")
    return _facade.stats()

# 초기화 메시지
import warnings
warnings.filterwarnings("default", category=DeprecationWarning)
# print 문 제거 - REPL 초기화 문제 해결
# print("AI Helpers v2.7.0 - Facade Pattern 적용 완료")
# print("새로운 사용법: h.<namespace>.<function>()")
