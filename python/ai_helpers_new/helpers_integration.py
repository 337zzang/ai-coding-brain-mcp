"""
AI Helpers New 통합 인터페이스 - Ultra Simple Version
극단순화된 버전으로 필수 기능만 유지
"""

# 백업 기능
from .backup_utils import (
    create_backup,
    restore_backup,
    list_backups,
    cleanup_old_backups
)

# 에러 메시지
from .error_messages import (
    get_error_message,
    format_error_response
)

# Context System
from .context_integration import get_context_integration
from .doc_context_helper import (
    create_doc_with_context,
    update_doc_with_context,
    suggest_related_docs_for_new,
    generate_doc_template
)


class FlowHelpers:
    """Flow 관련 헬퍼 함수 통합 클래스 - Ultra Simple Version"""

    # 백업 기능
    create_backup = staticmethod(create_backup)
    restore_backup = staticmethod(restore_backup)
    list_backups = staticmethod(list_backups)
    cleanup_old_backups = staticmethod(cleanup_old_backups)

    # 에러 메시지
    get_error_message = staticmethod(get_error_message)
    format_error_response = staticmethod(format_error_response)

    # Context System
    get_context_integration = staticmethod(get_context_integration)

    # 문서 헬퍼
    create_doc_with_context = staticmethod(create_doc_with_context)
    update_doc_with_context = staticmethod(update_doc_with_context)
    suggest_related_docs_for_new = staticmethod(suggest_related_docs_for_new)
    generate_doc_template = staticmethod(generate_doc_template)


# 싱글톤 인스턴스
flow_helpers = FlowHelpers()

# 간편 사용을 위한 별칭
fh = flow_helpers
