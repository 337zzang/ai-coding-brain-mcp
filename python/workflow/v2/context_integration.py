from typing import Dict, Any, Optional, TYPE_CHECKING
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if TYPE_CHECKING:
    from workflow.v2.models import WorkflowPlan, Task
from core.context_manager import ContextManager
from ai_helpers.helper_result import HelperResult
from workflow.v2.models import WorkflowPlan, Task, TaskStatus



class ContextIntegration:
    """ContextManager와 Workflow v2 시스템 간의 브릿지"""

    def __init__(self):
        self.context_manager: Optional[ContextManager] = None
        
        self._initialize()

    def _initialize(self):
        """컨텍스트 매니저 초기화"""
        try:
            from core.project_context import get_context_manager
            self.context_manager = get_context_manager()
        except ImportError:
            # 폴백: 직접 생성
            self.context_manager = ContextManager()

    def get_current_context(self) -> Dict[str, Any]:
        """현재 프로젝트 컨텍스트 가져오기"""
        if not self.context_manager:
            return {}

        return {
            'project_name': self.context_manager.current_project_name,
            'context_data': self.context_manager.context,
            'workflow_data': self.context_manager.workflow_data
        }

    def sync_workflow_to_context(self, workflow_plan: WorkflowPlan) -> HelperResult:
        """워크플로우 변경사항을 컨텍스트에 동기화"""
        try:
            if not self.context_manager:
                return HelperResult(False, error="ContextManager not initialized")

            # 워크플로우 데이터 업데이트
            workflow_data = {
                'current_plan': workflow_plan.to_dict() if workflow_plan else None,
                'last_updated': workflow_plan.updated_at if workflow_plan else None
            }

            # 컨텍스트 매니저에 저장
            self.context_manager.workflow_data = workflow_data

            # 파일에 저장
            if hasattr(self.context_manager, 'save_workflow'):
                self.context_manager.save_workflow()

            return HelperResult(True, data={'synced': True})

        except Exception as e:
            return HelperResult(False, error=f"Sync failed: {str(e)}")

    def load_workflow_from_context(self) -> Optional[WorkflowPlan]:
        """컨텍스트에서 워크플로우 로드"""
        try:
            if not self.context_manager or not self.context_manager.workflow_data:
                return None

            plan_data = self.context_manager.workflow_data.get('current_plan')
            if not plan_data:
                return None

            # WorkflowPlan 객체로 변환
            return WorkflowPlan.from_dict(plan_data)

        except Exception as e:
            print(f"Error loading workflow from context: {e}")
            return None

    def update_task_context(self, task: Task, action: str) -> HelperResult:
        """태스크 관련 컨텍스트 업데이트"""
        try:
            if not self.context_manager:
                return HelperResult(False, error="ContextManager not initialized")

            # 태스크 이벤트 기록
            task_event = {
                'action': action,
                'task_id': task.id,
                'task_title': task.title,
                'timestamp': task.updated_at
            }

            # 컨텍스트에 추가
            if 'task_events' not in self.context_manager.context:
                self.context_manager.context['task_events'] = []

            self.context_manager.context['task_events'].append(task_event)

            # 최근 10개만 유지
            self.context_manager.context['task_events'] = (
                self.context_manager.context['task_events'][-10:]
            )

            # 저장
            if hasattr(self.context_manager, 'save_all'):
                self.context_manager.save_all()

            return HelperResult(True, data={'event_recorded': True})

        except Exception as e:
            return HelperResult(False, error=f"Update failed: {str(e)}")

    def record_plan_archive(self, plan_name: str, plan_id: str, archived_at: str) -> HelperResult:
        """플랜 아카이브 이벤트 기록"""
        try:
            if not self.context_manager:
                return HelperResult(False, error="ContextManager not initialized")

            # 아카이브 이벤트 생성
            archive_event = {
                'action': 'plan_archived',
                'plan_name': plan_name,
                'plan_id': plan_id,
                'archived_at': archived_at,
                'timestamp': archived_at
            }

            # task_events에 추가
            if 'task_events' not in self.context_manager.context:
                self.context_manager.context['task_events'] = []

            self.context_manager.context['task_events'].append(archive_event)

            # 최근 10개만 유지
            self.context_manager.context['task_events'] = (
                self.context_manager.context['task_events'][-10:]
            )

            # 저장
            if hasattr(self.context_manager, 'save_all'):
                self.context_manager.save_all()

            print(f"📦 플랜 아카이브 이벤트 기록: {plan_name}")

            return HelperResult(True, data={'event_recorded': True})

        except Exception as e:
            return HelperResult(False, error=f"Archive event recording failed: {str(e)}")

    def switch_project_context(self, project_name: str) -> HelperResult:
        """프로젝트 컨텍스트 전환"""
        try:
            if not self.context_manager:
                return HelperResult(False, error="ContextManager not initialized")

            # 현재 컨텍스트 저장
            if hasattr(self.context_manager, 'save_all'):
                self.context_manager.save_all()

            # 새 프로젝트로 전환
            if hasattr(self.context_manager, 'switch_project'):
                self.context_manager.switch_project(project_name)

            return HelperResult(True, data={
                'switched_to': project_name,
                'previous_project': self.context_manager.current_project_name
            })

        except Exception as e:
            return HelperResult(False, error=f"Switch failed: {str(e)}")


# 싱글톤 인스턴스
_context_integration = None

def get_context_integration() -> ContextIntegration:
    """컨텍스트 통합 인스턴스 가져오기"""
    global _context_integration
    if _context_integration is None:
        _context_integration = ContextIntegration()
    return _context_integration


def sync_workflow_to_context():
    """워크플로우를 컨텍스트에 동기화 (wrapper 함수)"""
    try:
        integration = get_context_integration()
        # 현재 워크플로우 플랜 가져오기 - 일단 None으로 처리
        return integration.sync_workflow_to_context(None)
    except Exception as e:
        from python.ai_helpers.helper_result import HelperResult
        return HelperResult(False, error=str(e))
