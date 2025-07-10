"""
Optimized WorkflowManager for SSOT Architecture
==============================================

중복 저장을 제거하고 필요한 정보만 이벤트로 발행하도록 최적화된
WorkflowManager 확장입니다.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from python.workflow.v3.event_bus import event_bus
from python.workflow.v3.event_types import (
    EventType,
    create_plan_event,
    create_task_event,
    create_context_event
)

logger = logging.getLogger(__name__)


class OptimizedWorkflowEventAdapter:
    """
    최적화된 WorkflowEventAdapter

    필요한 정보만 이벤트에 포함하여 네트워크/메모리 사용을 줄입니다.
    """

    def __init__(self, workflow_manager):
        """
        Args:
            workflow_manager: WorkflowV3Manager 인스턴스
        """
        self.workflow_manager = workflow_manager
        self._last_save_time = None
        self._save_throttle_seconds = 5  # 저장 제한 시간

        logger.info("OptimizedWorkflowEventAdapter initialized")

    def publish_plan_created(self, plan):
        """플랜 생성 이벤트 발행 (최적화)"""
        # 필요한 정보만 포함
        event = create_plan_event(
            EventType.PLAN_CREATED,
            plan_id=plan.id,
            plan_name=plan.name,
            plan_status=plan.status.value,
            total_tasks=len(plan.tasks),
            project_name=self.workflow_manager.project_name
        )
        event_bus.publish(event)
        logger.debug(f"Published PLAN_CREATED (optimized): {plan.name}")

    def publish_task_completed(self, task, plan):
        """태스크 완료 이벤트 발행 (최적화)"""
        # 완료된 태스크 수 계산
        completed_tasks = sum(1 for t in plan.tasks if t.status.value == 'completed')

        event = create_task_event(
            EventType.TASK_COMPLETED,
            task_id=task.id,
            task_title=task.title,
            plan_id=plan.id,
            completed_tasks=completed_tasks,
            total_tasks=len(plan.tasks),
            project_name=self.workflow_manager.project_name
        )
        event_bus.publish(event)
        logger.debug(f"Published TASK_COMPLETED (optimized): {task.title}")

    def publish_context_sync(self):
        """컨텍스트 동기화 이벤트 발행 (스냅샷 정보만)"""
        plan = self.workflow_manager.state.current_plan

        if not plan:
            return

        # 스냅샷 정보만 전송
        completed_tasks = sum(1 for t in plan.tasks if t.status.value == 'completed')

        snapshot_data = {
            'current_plan_id': plan.id,
            'current_plan_name': plan.name,
            'total_tasks': len(plan.tasks),
            'completed_tasks': completed_tasks,
            'plan_status': plan.status.value,
            'timestamp': datetime.now().isoformat()
        }

        event = create_context_event(
            EventType.CONTEXT_UPDATED,
            context_type="workflow_snapshot",
            context_data=snapshot_data,
            project_name=self.workflow_manager.project_name
        )
        event_bus.publish(event)
        logger.debug("Published CONTEXT_UPDATED with snapshot")

    def should_save(self) -> bool:
        """저장 제한 확인 (throttling)"""
        if not self._last_save_time:
            return True

        elapsed = (datetime.now() - self._last_save_time).total_seconds()
        return elapsed >= self._save_throttle_seconds

    def mark_saved(self):
        """저장 시간 기록"""
        self._last_save_time = datetime.now()


def optimize_workflow_manager(workflow_manager):
    """
    기존 WorkflowManager에 최적화 적용

    - 중복 저장 방지
    - 이벤트 발행 최적화
    - 저장 빈도 제한
    """
    # 최적화된 어댑터 생성
    adapter = OptimizedWorkflowEventAdapter(workflow_manager)
    workflow_manager._optimized_adapter = adapter

    # 원본 save_data 메서드 저장
    original_save_data = workflow_manager.save_data

    # 최적화된 save_data
    def optimized_save_data():
        """최적화된 저장 (throttling 적용)"""
        if not adapter.should_save():
            logger.debug("Save throttled - skipping")
            return

        # 원본 저장 실행
        result = original_save_data()

        if result:
            adapter.mark_saved()
            # 스냅샷 동기화 이벤트 발행
            adapter.publish_context_sync()

        return result

    # 메서드 교체
    workflow_manager.save_data = optimized_save_data

    # 이벤트 발행 메서드도 최적화된 버전으로 교체
    def create_plan_optimized(*args, **kwargs):
        result = workflow_manager._original_create_plan(*args, **kwargs)
        if result and workflow_manager.state.current_plan:
            adapter.publish_plan_created(workflow_manager.state.current_plan)
        return result

    def complete_task_optimized(task_id: str, *args, **kwargs):
        # 태스크 찾기
        task = None
        plan = workflow_manager.state.current_plan
        if plan:
            for t in plan.tasks:
                if t.id == task_id:
                    task = t
                    break

        result = workflow_manager._original_complete_task(task_id, *args, **kwargs)

        if result and task and plan:
            adapter.publish_task_completed(task, plan)

        return result

    # 원본 메서드 백업
    if not hasattr(workflow_manager, '_original_create_plan'):
        workflow_manager._original_create_plan = workflow_manager.create_plan
        workflow_manager._original_complete_task = workflow_manager.complete_task

    # 메서드 교체
    workflow_manager.create_plan = create_plan_optimized
    workflow_manager.complete_task = complete_task_optimized

    logger.info("WorkflowManager optimized for SSOT architecture")

    return adapter


class WorkflowDataMigrator:
    """
    레거시 데이터 마이그레이션 도구

    ContextManager의 workflow.json 데이터를 
    WorkflowManager로 이전합니다.
    """

    @staticmethod
    def migrate_legacy_workflow_data(context_path: str = "memory"):
        """레거시 workflow.json 데이터 마이그레이션"""
        from pathlib import Path
        import json

        legacy_file = Path(context_path) / "workflow.json"

        if not legacy_file.exists():
            logger.info("No legacy workflow.json to migrate")
            return

        try:
            with open(legacy_file, 'r', encoding='utf-8') as f:
                legacy_data = json.load(f)

            logger.info(f"Found legacy workflow data for {len(legacy_data)} projects")

            # 백업 생성
            backup_file = legacy_file.with_suffix(f'.json.migrated_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            legacy_file.rename(backup_file)

            logger.info(f"Legacy data backed up to: {backup_file}")

            # 각 프로젝트의 데이터는 WorkflowManager가 처리하도록 남김
            # (실제 마이그레이션은 WorkflowManager 인스턴스 생성 시)

            return legacy_data

        except Exception as e:
            logger.error(f"Error migrating legacy data: {e}")
            return None


# 싱글톤 최적화 관리자
_optimization_applied = set()

def ensure_workflow_optimization(workflow_manager):
    """WorkflowManager 최적화 확인 및 적용"""
    manager_id = id(workflow_manager)

    if manager_id not in _optimization_applied:
        optimize_workflow_manager(workflow_manager)
        _optimization_applied.add(manager_id)
        logger.debug(f"Optimization applied to WorkflowManager {manager_id}")
