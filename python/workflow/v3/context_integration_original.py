"""
Workflow v3 컨텍스트 연동
최소 정보만 동기화하는 간소화된 연동 모듈
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .models import WorkflowPlan, Task, WorkflowEvent, EventType
from python.ai_helpers.helper_result import HelperResult

logger = logging.getLogger(__name__)


class ContextIntegration:
    """워크플로우와 프로젝트 컨텍스트 간의 간소화된 연동"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.context_manager = None
        self._initialize()
        
    def _initialize(self):
        """컨텍스트 매니저 초기화"""
        try:
            # 컨텍스트 매니저 import 시도
            from python.core.context_manager import ContextManager
            self.context_manager = ContextManager(self.project_name)
            logger.info("ContextManager initialized")
        except ImportError:
            logger.warning("ContextManager not available, running without context integration")
            self.context_manager = None
        except Exception as e:
            logger.error(f"Failed to initialize ContextManager: {e}")
            self.context_manager = None
            
    def is_available(self) -> bool:
        """컨텍스트 연동 가능 여부"""
        return self.context_manager is not None
        
    def sync_plan_summary(self, plan: Optional[WorkflowPlan]) -> bool:
        """현재 플랜의 요약 정보만 동기화
        
        Args:
            plan: 현재 워크플로우 플랜
            
        Returns:
            성공 여부
        """
        if not self.is_available():
            return True  # 연동 없어도 성공으로 처리
            
        try:
            if plan:
                # 최소한의 정보만 전달
                summary = {
                    'plan_id': plan.id,
                    'plan_name': plan.name,
                    'status': plan.status.value,
                    'total_tasks': len(plan.tasks),
                    'completed_tasks': len([t for t in plan.tasks if t.status.value == 'completed']),
                    'updated_at': plan.updated_at.isoformat()
                }
            else:
                summary = None
                
            # 컨텍스트에 업데이트
            self.context_manager.update_workflow_summary(summary)
            
            logger.debug(f"Synced plan summary: {plan.name if plan else 'None'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync plan summary: {e}")
            return False

            
    def record_event(self, event: WorkflowEvent) -> bool:
        """중요 이벤트만 컨텍스트에 기록
        
        Args:
            event: 워크플로우 이벤트
            
        Returns:
            성공 여부
        """
        if not self.is_available():
            return True
            
        try:
            # 중요 이벤트만 선택적으로 기록
            important_events = {
                EventType.PLAN_CREATED,
                EventType.PLAN_COMPLETED,
                EventType.PLAN_ARCHIVED,
                EventType.TASK_COMPLETED
            }
            
            if event.type not in important_events:
                return True  # 중요하지 않은 이벤트는 스킵
                
            # 이벤트 요약 생성
            event_summary = {
                'type': event.type.value,
                'timestamp': event.timestamp.isoformat(),
                'details': self._extract_event_details(event)
            }
            
            # 컨텍스트에 이벤트 추가
            self.context_manager.add_workflow_event(event_summary)
            
            logger.debug(f"Recorded event: {event.type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record event: {e}")
            return False
            
    def _extract_event_details(self, event: WorkflowEvent) -> Dict[str, Any]:
        """이벤트에서 핵심 정보만 추출
        
        Args:
            event: 워크플로우 이벤트
            
        Returns:
            핵심 정보 딕셔너리
        """
        details = {}
        
        if event.type == EventType.PLAN_CREATED:
            details['plan_name'] = event.details.get('name', 'Unknown')
            
        elif event.type == EventType.PLAN_COMPLETED:
            details['plan_name'] = event.details.get('name', 'Unknown')
            details['total_tasks'] = event.details.get('total_tasks', 0)
            details['completed_tasks'] = event.details.get('completed_tasks', 0)
            
        elif event.type == EventType.PLAN_ARCHIVED:
            details['plan_name'] = event.details.get('name', 'Unknown')
            
        elif event.type == EventType.TASK_COMPLETED:
            details['task_title'] = event.details.get('title', 'Unknown')
            details['duration'] = event.details.get('duration', 0)
            
        return details

            
    def get_current_task_context(self, task: Optional[Task]) -> Dict[str, Any]:
        """현재 태스크의 컨텍스트 정보 조회
        
        Args:
            task: 현재 태스크
            
        Returns:
            태스크 컨텍스트 정보
        """
        if not task:
            return {}
            
        context = {
            'task_id': task.id,
            'task_title': task.title,
            'task_description': task.description,
            'task_status': task.status.value
        }
        
        # 컨텍스트 매니저에서 추가 정보 가져오기
        if self.is_available():
            try:
                # 관련 파일, 최근 활동 등 추가 정보
                additional_context = self.context_manager.get_task_context(task.id)
                if additional_context:
                    context.update(additional_context)
            except Exception as e:
                logger.error(f"Failed to get task context: {e}")
                
        return context
        
    def clear_workflow_context(self) -> bool:
        """워크플로우 관련 컨텍스트 정보 초기화
        
        Returns:
            성공 여부
        """
        if not self.is_available():
            return True
            
        try:
            self.context_manager.clear_workflow_data()
            logger.info("Cleared workflow context")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear workflow context: {e}")
            return False
            
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 워크플로우 활동 조회
        
        Args:
            limit: 조회할 활동 수
            
        Returns:
            최근 활동 목록
        """
        if not self.is_available():
            return []
            
        try:
            return self.context_manager.get_recent_workflow_events(limit)
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []


# 간단한 Mock ContextManager (실제 구현이 없을 때 사용)
class MockContextManager:
    """테스트용 Mock 컨텍스트 매니저"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.workflow_summary = None
        self.workflow_events = []
        
    def update_workflow_summary(self, summary: Optional[Dict[str, Any]]) -> None:
        self.workflow_summary = summary
        
    def add_workflow_event(self, event: Dict[str, Any]) -> None:
        self.workflow_events.append(event)
        # 최근 20개만 유지
        if len(self.workflow_events) > 20:
            self.workflow_events = self.workflow_events[-20:]
            
    def get_task_context(self, task_id: str) -> Dict[str, Any]:
        return {}
        
    def clear_workflow_data(self) -> None:
        self.workflow_summary = None
        self.workflow_events.clear()
        
    def get_recent_workflow_events(self, limit: int) -> List[Dict[str, Any]]:
        return self.workflow_events[-limit:]
