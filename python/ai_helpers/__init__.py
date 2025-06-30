"""AIHelpers 모듈 패키지

이 패키지는 AI Coding Brain의 헬퍼 함수들을 모듈별로 구성합니다.
"""

# Git 함수들
from .git import (
    git_status, git_add, git_commit, git_branch,
    git_stash, git_stash_pop, git_log
)

# Build 함수들
from .build import (
    find_executable, detect_project_type, run_command,
    build_project, install_dependencies
)

# Context 함수들
from .context import (
    get_context, get_value, initialize_context, 
    update_cache, save_context
)

# Command 함수들
from .command import (
    cmd_plan, cmd_task, cmd_next, cmd_flow,
    track_file_access, track_function_edit, 
    get_work_tracking_summary
)

# File 함수들
from .file import (
    create_file, read_file, write_file, append_to_file
)

# Code 함수들
from .code import (
    replace_block, insert_block, parse_code,
    parse_with_snippets, get_snippet_preview
)

# Search 함수들
from .search import (
    scan_directory_dict, search_files_advanced, search_code_content
)

# Utils
from .utils import list_functions

__all__ = [
    # Git
    'git_status', 'git_add', 'git_commit', 'git_branch',
    'git_stash', 'git_stash_pop', 'git_log',
    # Build
    'find_executable', 'detect_project_type', 'run_command',
    'build_project', 'install_dependencies',
    # Context
    'get_context', 'get_value', 'initialize_context', 'update_cache', 'save_context',
    # Command
    'cmd_plan', 'cmd_task', 'cmd_next', 'cmd_flow',
    'track_file_access', 'track_function_edit', 'get_work_tracking_summary',
    # File
    'create_file', 'read_file', 'write_file', 'append_to_file',
    # Code
    'replace_block', 'insert_block', 'parse_code', 'parse_with_snippets', 'get_snippet_preview',
    # Search
    'scan_directory_dict', 'search_files_advanced', 'search_code_content',
    # Utils
    'list_functions'
]
