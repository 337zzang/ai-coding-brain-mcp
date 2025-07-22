"""
AI Helpers New 통합 인터페이스
기존 helpers 객체처럼 사용할 수 있도록 통합
"""

# 백업 기능
from .backup_utils import (
    create_backup,
    restore_backup,
    list_backups,
    cleanup_old_backups
)

# Plan 자동 완료
from .plan_auto_complete import (
    check_and_complete_plan,
    check_plan_after_task_complete
)

# 에러 메시지
from .error_messages import (
    get_error_message,
    format_error_response
)

# Context System
from .context_integration import get_context_integration
from .flow_context_wrapper import (
    record_flow_action,
    record_task_action,
    record_plan_action,
    record_doc_creation,
    record_doc_update,
    get_related_docs,
    get_flow_context_summary,
    get_docs_context_summary,
    with_context
)
from .doc_context_helper import (
    create_doc_with_context,
    update_doc_with_context,
    suggest_related_docs_for_new,
    generate_doc_template
)

# 검색/필터
from .flow_search import (
    FlowSearchEngine,
    search_flows_by_name,
    get_active_flows,
    get_flows_with_pending_tasks,
    get_recent_flows
)

# 일괄 작업
from .flow_batch import (
    FlowBatchProcessor,
    batch_complete_all_todo_tasks,
    batch_skip_error_tasks,
    batch_cleanup_empty_plans,
    batch_add_default_tasks
)

# Flow 관리
from .flow_manager_unified import FlowManagerUnified

class FlowHelpers:
    """Flow 관련 헬퍼 함수 통합 클래스"""

    # 백업 기능
    create_backup = staticmethod(create_backup)
    restore_backup = staticmethod(restore_backup)
    list_backups = staticmethod(list_backups)
    cleanup_old_backups = staticmethod(cleanup_old_backups)

    # Plan 자동 완료
    check_and_complete_plan = staticmethod(check_and_complete_plan)
    check_plan_after_task_complete = staticmethod(check_plan_after_task_complete)

    # 에러 메시지
    get_error_message = staticmethod(get_error_message)
    format_error_response = staticmethod(format_error_response)

    # Context System
    get_context_integration = staticmethod(get_context_integration)
    record_flow_action = staticmethod(record_flow_action)
    record_task_action = staticmethod(record_task_action)
    record_plan_action = staticmethod(record_plan_action)
    record_doc_creation = staticmethod(record_doc_creation)
    record_doc_update = staticmethod(record_doc_update)
    get_related_docs = staticmethod(get_related_docs)
    get_flow_context_summary = staticmethod(get_flow_context_summary)
    get_docs_context_summary = staticmethod(get_docs_context_summary)

    # 문서 헬퍼
    create_doc_with_context = staticmethod(create_doc_with_context)
    update_doc_with_context = staticmethod(update_doc_with_context)
    suggest_related_docs_for_new = staticmethod(suggest_related_docs_for_new)
    generate_doc_template = staticmethod(generate_doc_template)

    # 검색/필터
    @staticmethod
    def create_search_engine():
        """검색 엔진 인스턴스 생성"""
        return FlowSearchEngine()

    search_flows_by_name = staticmethod(search_flows_by_name)
    get_active_flows = staticmethod(get_active_flows)
    get_flows_with_pending_tasks = staticmethod(get_flows_with_pending_tasks)
    get_recent_flows = staticmethod(get_recent_flows)

    # 일괄 작업
    @staticmethod
    def create_batch_processor(dry_run=False):
        """일괄 작업 프로세서 생성"""
        processor = FlowBatchProcessor()
        if dry_run:
            processor.set_dry_run(True)
        return processor

    batch_complete_all_todo_tasks = staticmethod(batch_complete_all_todo_tasks)
    batch_skip_error_tasks = staticmethod(batch_skip_error_tasks)
    batch_cleanup_empty_plans = staticmethod(batch_cleanup_empty_plans)
    batch_add_default_tasks = staticmethod(batch_add_default_tasks)

    # Flow Manager
    @staticmethod
    def create_flow_manager():
        """FlowManagerUnified 인스턴스 생성"""
        return FlowManagerUnified()

# 싱글톤 인스턴스
flow_helpers = FlowHelpers()

# 간편 사용을 위한 별칭
fh = flow_helpers
