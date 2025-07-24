"""
AI Helpers New - Flow 시스템 v2.1 (헬퍼 함수 복원)
레거시 제거 버전에서 필수 헬퍼 함수들을 다시 추가
"""

# 도메인 모델
from .domain.models import Flow, Plan, Task, TaskStatus

# 저장소
from .repository.json_repository import JsonRepository

# 서비스
from .service.flow_service import FlowService

# 매니저
from .flow_manager import FlowManager

# 명령어
from .commands import CommandRouter, command

# 워크플로우
from .workflow_commands import (
    wf, 
    help_wf,
    current_flow,
    current_project,
    set_project,
    get_flow_manager
)

# Context 통합
from .context_integration import ContextIntegration
from .flow_context_wrapper import (
    record_flow_action, record_task_action, record_plan_action,
    record_doc_creation, record_doc_update
)

# 레거시 호환
from .flow_manager_unified import FlowManagerUnified
from .legacy_flow_adapter import LegacyFlowAdapter

# 헬퍼 함수들 - v2.1에서 복원
from .file import read, write, append, read_json, write_json, exists, info
from .code import parse, view, replace, insert, functions, classes
from .search import search_files, search_code, find_function, find_class, grep
from .llm import ask_o3_async, check_o3_status, get_o3_result, show_o3_progress
from .git import (
    git_status, git_add, git_commit, git_push, git_pull, 
    git_branch, git_log, git_current_branch, git_diff
)
from .util import ok, err, is_ok, get_data, get_error
from .project import get_current_project, fp, scan_directory, scan_directory_dict

# 헬퍼 통합
from .helpers_integration import FlowHelpers, flow_helpers, fh

# 초기화
import logging
logging.basicConfig(level=logging.INFO)

__version__ = "2.1.0"

__all__ = [
    # 핵심
    'FlowManager',
    'CommandRouter',
    'wf',
    'help_wf',

    # 모델
    'Flow',
    'Plan', 
    'Task',
    'TaskStatus',

    # 유틸리티
    'current_flow',
    'current_project',
    'set_project',

    # 레거시 호환
    'FlowManagerUnified',
    'LegacyFlowAdapter',
    'ContextIntegration',

    # 파일 I/O
    'read', 'write', 'append', 'read_json', 'write_json', 'exists', 'info',

    # 코드 분석
    'parse', 'view', 'replace', 'insert', 'functions', 'classes',

    # 검색
    'search_files', 'search_code', 'find_function', 'find_class', 'grep',

    # LLM
    'ask_o3_async', 'check_o3_status', 'get_o3_result', 'show_o3_progress',

    # Git
    'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
    'git_branch', 'git_log', 'git_current_branch', 'git_diff',

    # 유틸리티
    'ok', 'err', 'is_ok', 'get_data', 'get_error',

    # 프로젝트
    'get_current_project', 'fp', 'scan_directory', 'scan_directory_dict',

    # Context
    'record_flow_action', 'record_task_action', 'record_plan_action',
    'record_doc_creation', 'record_doc_update',

    # 헬퍼 통합
    'FlowHelpers', 'flow_helpers', 'fh'
]

print("✅ Flow 시스템 v2.1 로드됨 - 헬퍼 함수 복원 완료")
