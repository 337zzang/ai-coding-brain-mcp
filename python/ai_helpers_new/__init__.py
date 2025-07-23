"""
AI Helpers New - 리팩토링된 Flow 시스템

레거시 호환성:
    # 중복 import 제거됨

새 코드에서 권장:
    from ai_helpers_new.service import FlowService, PlanService, TaskService

추가 기능:
    from ai_helpers_new import backup_utils, flow_search, flow_batch
"""

# 레거시 호환성을 위한 export
from .flow_manager_unified import FlowManagerUnified

# 새 구조 export
from .domain.models import Flow, Plan, Task, TaskStatus
from .infrastructure.flow_repository import JsonFlowRepository, InMemoryFlowRepository
from .service.plan_service import PlanService
from .service.task_service import TaskService
# from .presentation.command_processor import CommandProcessor  # 사용 안 함

# 추가 기능 모듈들
from . import backup_utils
from . import flow_backup_wrapper
from . import plan_auto_complete
from . import error_messages
from . import context_integration
from . import flow_context_wrapper
from . import doc_context_helper
from . import flow_search
from . import flow_batch

# 주요 함수들을 직접 export (편의성)
from .backup_utils import create_backup, restore_backup, list_backups, cleanup_old_backups
from .plan_auto_complete import check_and_complete_plan, check_plan_after_task_complete
from .error_messages import get_error_message, format_error_response
from .context_integration import get_context_integration
from .flow_context_wrapper import (
    record_flow_action, record_task_action, record_plan_action,
    record_doc_creation, record_doc_update, get_related_docs,
    get_flow_context_summary, get_docs_context_summary
)
from .doc_context_helper import (
    create_doc_with_context, update_doc_with_context,
    suggest_related_docs_for_new, generate_doc_template
)
from .flow_search import (
    FlowSearchEngine, search_flows_by_name, get_active_flows,
    get_flows_with_pending_tasks, get_recent_flows
)
from .flow_batch import (
    FlowBatchProcessor, batch_complete_all_todo_tasks,
    batch_skip_error_tasks, batch_cleanup_empty_plans,
    batch_add_default_tasks
)


# 헬퍼 통합 인터페이스
from .helpers_integration import FlowHelpers, flow_helpers, fh

# 실제 헬퍼 함수들 import
from .file import read, write, append, read_json, write_json, exists, info, list_directory
from .code import parse, view, replace, insert, functions, classes
from .search import search_files, search_code, find_function, find_class, grep, find_in_file
from .llm import ask_o3_async, check_o3_status, get_o3_result, show_o3_progress, save_o3_result, list_o3_tasks, clear_completed_tasks, prepare_o3_context
from .git import git_status, git_add, git_commit, git_push, git_pull, git_branch, git_log, git_current_branch, git_diff, git_status_string
from .util import ok, err, is_ok, get_data, get_error
from .project import get_current_project, fp, scan_directory, detect_project_type, scan_directory_dict, create_project_structure

__all__ = [
    # 레거시
    'FlowManagerUnified',

    # 도메인 모델
    'Flow', 'Plan', 'Task', 'TaskStatus',

    # 저장소
    'JsonFlowRepository', 'InMemoryFlowRepository',

    # 서비스

    # 프레젠테이션
    # 'CommandProcessor',  # 사용 안 함

    # 백업 기능
    'backup_utils',
    'create_backup', 'restore_backup', 'list_backups', 'cleanup_old_backups',

    # Plan 자동 완료
    'plan_auto_complete',
    'check_and_complete_plan', 'check_plan_after_task_complete',

    # 에러 메시지
    'error_messages',
    'get_error_message', 'format_error_response',

    # Context System
    'context_integration', 'flow_context_wrapper', 'doc_context_helper',
    'get_context_integration',
    'record_flow_action', 'record_task_action', 'record_plan_action',
    'record_doc_creation', 'record_doc_update', 'get_related_docs',
    'create_doc_with_context', 'update_doc_with_context',
    'suggest_related_docs_for_new', 'generate_doc_template',
    'get_flow_context_summary', 'get_docs_context_summary',

    # 검색/필터
    'flow_search',
    'FlowSearchEngine', 'search_flows_by_name', 'get_active_flows',
    'get_flows_with_pending_tasks', 'get_recent_flows',

    # 일괄 작업
    'flow_batch',
    'FlowBatchProcessor', 'batch_complete_all_todo_tasks',
    'batch_skip_error_tasks', 'batch_cleanup_empty_plans',
    'batch_add_default_tasks',
    
    # 헬퍼 통합
    'FlowHelpers', 'flow_helpers', 'fh',
    
    # 파일 작업
    'read', 'write', 'append', 'read_json', 'write_json', 'exists', 'info', 'list_directory',
    
    # 코드 분석/수정
    'parse', 'view', 'replace', 'insert', 'functions', 'classes',
    
    # 검색
    'search_files', 'search_code', 'find_function', 'find_class', 'grep',
    
    # LLM
    'ask_o3_async', 'check_o3_status', 'get_o3_result', 'show_o3_progress',
    
    # Git
    'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull', 'git_branch', 'git_log', 'git_current_branch',
    
    # 유틸리티
    'ok', 'err', 'is_ok', 'get_data', 'get_error',
    
    # 프로젝트
    'get_current_project', 'fp', 'scan_directory',
    # 추가 헬퍼 함수들
    'find_in_file', 'git_diff',
    'save_o3_result', 'list_o3_tasks', 'clear_completed_tasks', 'prepare_o3_context',
    'detect_project_type', 'scan_directory_dict', 'create_project_structure',
]
