"""
State Manager for Workflow
==========================
워크플로우와 태스크의 상태를 관리
"""

from typing import Dict, Optional, List
from enum import Enum
import time


class WorkflowState(Enum):
    """워크플로우 상태"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class TaskState(Enum):
    """태스크 상태"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class StateManager:
    """상태 관리자"""

    def __init__(self):
        self.workflow_states: Dict[str, WorkflowState] = {}
        self.task_states: Dict[str, TaskState] = {}
        self.state_history: List[Dict] = []

    def set_workflow_state(self, workflow_id: str, new_state: WorkflowState) -> Optional[str]:
        """워크플로우 상태 설정"""
        old_state = self.workflow_states.get(workflow_id)

        # 상태 전이 유효성 검사
        if not self._is_valid_workflow_transition(old_state, new_state):
            return None

        self.workflow_states[workflow_id] = new_state

        # 히스토리 기록
        self._record_transition('workflow', workflow_id, 
                              old_state.value if old_state else None, 
                              new_state.value)

        return f"{old_state.value if old_state else 'none'}>{new_state.value}"

    def set_task_state(self, task_id: str, new_state: TaskState) -> Optional[str]:
        """태스크 상태 설정"""
        old_state = self.task_states.get(task_id)

        # 상태 전이 유효성 검사
        if not self._is_valid_task_transition(old_state, new_state):
            return None

        self.task_states[task_id] = new_state

        # 히스토리 기록
        self._record_transition('task', task_id,
                              old_state.value if old_state else None,
                              new_state.value)

        return f"{old_state.value if old_state else 'none'}>{new_state.value}"

    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """워크플로우 상태 조회"""
        return self.workflow_states.get(workflow_id)

    def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """태스크 상태 조회"""
        return self.task_states.get(task_id)

    def _is_valid_workflow_transition(self, old: Optional[WorkflowState], 
                                    new: WorkflowState) -> bool:
        """워크플로우 상태 전이 유효성 검사"""
        if old is None:  # 새로운 워크플로우
            return new in [WorkflowState.DRAFT, WorkflowState.ACTIVE]

        # 유효한 전이 규칙
        valid_transitions = {
            WorkflowState.DRAFT: [WorkflowState.ACTIVE, WorkflowState.ARCHIVED],
            WorkflowState.ACTIVE: [WorkflowState.COMPLETED, WorkflowState.FAILED],
            WorkflowState.COMPLETED: [WorkflowState.ARCHIVED],
            WorkflowState.FAILED: [WorkflowState.ARCHIVED],
            WorkflowState.ARCHIVED: []  # 보관된 후에는 변경 불가
        }

        return new in valid_transitions.get(old, [])

    def _is_valid_task_transition(self, old: Optional[TaskState], 
                                new: TaskState) -> bool:
        """태스크 상태 전이 유효성 검사"""
        if old is None:  # 새로운 태스크
            return new == TaskState.PENDING

        # 유효한 전이 규칙
        valid_transitions = {
            TaskState.PENDING: [TaskState.ACTIVE, TaskState.BLOCKED],
            TaskState.ACTIVE: [TaskState.COMPLETED, TaskState.FAILED, TaskState.BLOCKED],
            TaskState.COMPLETED: [],  # 완료 후 변경 불가
            TaskState.FAILED: [TaskState.PENDING],  # 재시도 가능
            TaskState.BLOCKED: [TaskState.PENDING, TaskState.ACTIVE]
        }

        return new in valid_transitions.get(old, [])

    def _record_transition(self, entity_type: str, entity_id: str,
                         old_state: Optional[str], new_state: str):
        """상태 전이 기록"""
        self.state_history.append({
            'type': entity_type,
            'entity_id': entity_id,
            'old_state': old_state,
            'new_state': new_state,
            'timestamp': time.time()
        })
