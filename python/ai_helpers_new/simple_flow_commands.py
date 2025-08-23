"""
Flow Commands - 호환성 래퍼
분리일: 2025-08-03

이 파일은 레거시 호환성을 위해 유지됩니다.
실제 구현은 다음 모듈들로 분리되었습니다:
- flow_api.py: 핵심 비즈니스 로직 (FlowAPI 클래스)
- flow_cli.py: CLI 인터페이스 (flow 함수)
- flow_views.py: 출력 및 포맷팅
- flow_manager_utils.py: Manager 유틸리티

원본 크기: 1,262줄 (49,182 bytes)
분리 후: ~50줄
"""

# 모든 기능을 분리된 모듈에서 import
from .flow_api import FlowAPI
from .flow_cli import (
    flow, get_flow_api_instance, handle_task_command,
    select_plan, create_plan, delete_plan, switch_project
)
from .flow_views import (
    show_status, show_plans, show_tasks, 
    display_task_history, _show_project_summary
)
from .flow_manager_utils import (
    get_manager, get_current_plan_id, set_current_plan_id
)

# 레거시 호환성을 위한 전역 변수 (사용 지양)
_manager = None
_flow_api_instance = None

# 모든 공개 API export
__all__ = [
    # API
    'FlowAPI',
    'get_flow_api_instance',

    # CLI
    'flow',
    'handle_task_command',
    'select_plan',
    'create_plan', 
    'delete_plan',
    'switch_project',

    # Views
    'show_status',
    'show_plans',
    'show_tasks',
    'display_task_history',

    # Utils
    'get_manager',
    'get_current_plan_id',
    'set_current_plan_id',
]

# 사용 지침
if __name__ == "__main__":
    print("Flow 시스템이 모듈별로 분리되었습니다.")
    print("- 비즈니스 로직: flow_api.FlowAPI")
    print("- CLI: flow_cli.flow()")
    print("- 출력: flow_views.*")
    print("- 유틸리티: flow_manager_utils.*")

def help_flow():
    """Flow 시스템 도움말"""
    return {
        'ok': True,
        'data': {
            'commands': {
                '/status': 'Show current status',
                '/plans': 'List all plans',
                '/tasks': 'List tasks for current plan',
                '/next': 'Move to next task',
                '/done': 'Complete current task',
                '/create': 'Create new plan',
                '/select': 'Select a plan',
                '/delete': 'Delete a plan'
            }
        }
    }
