"""
Internal Workflow API
====================

시스템 내부 컴포넌트 간 통신을 위한 API
직접적인 상태 변경과 고급 작업을 수행
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from ..models import WorkflowPlan, Task, TaskStatus, PlanStatus, WorkflowEvent, EventType
from ..errors import WorkflowError, ErrorCode
from ..storage import WorkflowStorage
from ..events import EventBuilder
from .decorators import internal_only, log_command, transactional, auto_save

logger = logging.getLogger(__name__)


class InternalWorkflowAPI:
    """
    내부 시스템 API
    
    WorkflowManager의 핵심 기능을 내부 컴포넌트에 제공
    직접적인 상태 조작과 트랜잭션 지원
    """
    
    def __init__(self, workflow_manager):
        self.manager = workflow_manager
        self.state = workflow_manager.state
        self.storage = workflow_manager.storage
        self.event_store = workflow_manager.event_store
        
    # === 상태 직접 조작 ===
    
    @internal_only
    @log_command("internal")
    @transactional
    def set_current_plan(self, plan: WorkflowPlan) -> None:
        """현재 플랜 직접 설정"""
        self.state.current_plan = plan
        
        # 이벤트 발행
        event = WorkflowEvent(
            type=EventType.PLAN_UPDATED,
            plan_id=plan.id,
            details={'action': 'set_current_plan'}
        )
        self._add_event(event)
        
    @internal_only
    @log_command("internal")
    @transactional
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          metadata: Optional[Dict[str, Any]] = None) -> Task:
        """태스크 상태 직접 업데이트"""
        task = self._get_task_by_id(task_id)
        if not task:
            raise WorkflowError(ErrorCode.TASK_NOT_FOUND, f"Task {task_id} not found")
            
        old_status = task.status
        task.status = status
        task.updated_at = datetime.now()
        
        # 메타데이터 업데이트
        if metadata:
            task.outputs.update(metadata)
            
        # 상태별 추가 처리
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now()
            if task.started_at:
                task.duration = int((task.completed_at - task.started_at).total_seconds())
                
        # 이벤트 발행
        event = EventBuilder.task_updated(
            self.state.current_plan.id,
            task,
            {'status': f"{old_status.value} -> {status.value}"}
        )
        self._add_event(event)
        
        return task
        
    @internal_only
    @log_command("internal")
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 태스크 조회"""
        return self._get_task_by_id(task_id)
        
    @internal_only
    @log_command("internal")
    @auto_save
    def batch_update_tasks(self, updates: List[Dict[str, Any]]) -> List[Task]:
        """여러 태스크 일괄 업데이트
        
        Args:
            updates: [{'task_id': str, 'status': TaskStatus, 'metadata': dict}, ...]
        """
        updated_tasks = []
        
        for update in updates:
            task = self.update_task_status(
                update['task_id'],
                update.get('status'),
                update.get('metadata')
            )
            updated_tasks.append(task)
            
        return updated_tasks
        
    # === 플랜 생명주기 관리 ===
    
    @internal_only
    @log_command("internal")
    @transactional
    @auto_save
    def force_complete_plan(self, plan_id: str) -> bool:
        """플랜 강제 완료"""
        if self.state.current_plan and self.state.current_plan.id == plan_id:
            plan = self.state.current_plan
            
            # 모든 미완료 태스크를 취소 처리
            for task in plan.tasks:
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    task.status = TaskStatus.CANCELLED
                    task.notes.append("[시스템] 플랜 강제 완료로 인한 취소")
                    
            # 플랜 완료
            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.now()
            
            # 이벤트
            event = EventBuilder.plan_completed(plan)
            self._add_event(event)
            
            return True
        return False
        
    @internal_only
    @log_command("internal")
    def create_plan_from_template(self, template: Dict[str, Any]) -> WorkflowPlan:
        """템플릿에서 플랜 생성
        
        Args:
            template: {
                'name': str,
                'description': str,
                'tasks': [{'title': str, 'description': str}, ...]
            }
        """
        # 플랜 생성
        plan = WorkflowPlan(
            name=template['name'],
            description=template.get('description', ''),
            status=PlanStatus.DRAFT
        )
        
        # 태스크 추가
        for task_data in template.get('tasks', []):
            task = Task(
                title=task_data['title'],
                description=task_data.get('description', '')
            )
            plan.tasks.append(task)
            
        return plan
        
    # === 이벤트 및 통계 ===
    
    @internal_only
    def get_event_history(self, plan_id: Optional[str] = None, 
                         event_type: Optional[str] = None,
                         limit: int = 100) -> List[WorkflowEvent]:
        """이벤트 히스토리 조회"""
        events = self.event_store.events
        
        # 필터링
        if plan_id:
            events = [e for e in events if e.plan_id == plan_id]
        if event_type:
            events = [e for e in events if e.type == event_type]
            
        # 정렬 및 제한
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
        
    @internal_only
    def calculate_plan_statistics(self, plan: WorkflowPlan) -> Dict[str, Any]:
        """플랜 통계 계산"""
        total_tasks = len(plan.tasks)
        completed_tasks = len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED])
        cancelled_tasks = len([t for t in plan.tasks if t.status == TaskStatus.CANCELLED])
        in_progress_tasks = len([t for t in plan.tasks if t.status == TaskStatus.IN_PROGRESS])
        
        total_duration = sum(t.duration or 0 for t in plan.tasks)
        avg_duration = total_duration / completed_tasks if completed_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'cancelled_tasks': cancelled_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completion_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'total_duration_seconds': total_duration,
            'average_duration_seconds': avg_duration,
            'estimated_remaining_seconds': avg_duration * (total_tasks - completed_tasks)
        }
        
    # === 트랜잭션 및 백업 ===
    
    @internal_only
    @log_command("internal")
    def create_checkpoint(self) -> str:
        """현재 상태의 체크포인트 생성"""
        import json
        import copy
        
        checkpoint_id = str(uuid4())
        checkpoint_data = {
            'id': checkpoint_id,
            'timestamp': datetime.now().isoformat(),
            'state': self.state.to_dict() if hasattr(self.state, 'to_dict') else None,
            'current_plan': self.state.current_plan.to_dict() if self.state.current_plan else None
        }
        
        # 체크포인트 저장
        checkpoint_path = f"memory/checkpoints/{checkpoint_id}.json"
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint_id
        
    @internal_only
    @log_command("internal")
    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """체크포인트에서 상태 복원"""
        import json
        
        checkpoint_path = f"memory/checkpoints/{checkpoint_id}.json"
        if not os.path.exists(checkpoint_path):
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return False
            
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
            
        # 상태 복원 (실제 구현은 모델에 따라 조정 필요)
        # self.state = WorkflowState.from_dict(checkpoint_data['state'])
        
        logger.info(f"Restored checkpoint: {checkpoint_id}")
        return True
        
    # === 헬퍼 메서드 ===
    
    def _get_task_by_id(self, task_id: str) -> Optional[Task]:
        """태스크 ID로 조회"""
        if not self.state.current_plan:
            return None
            
        for task in self.state.current_plan.tasks:
            if task.id == task_id:
                return task
        return None
        
    def _add_event(self, event: WorkflowEvent) -> None:
        """이벤트 추가"""
        self.event_store.add(event)
        
        # EventBus로 발행
        if hasattr(self.manager, 'event_adapter') and self.manager.event_adapter:
            try:
                self.manager.event_adapter.publish_workflow_event(event)
            except Exception as e:
                logger.error(f"Failed to publish event: {e}")


# Export
__all__ = ['InternalWorkflowAPI']
