"""
Context Manager - SSOT Architecture
===================================

단일 진실 원천(SSOT) 아키텍처를 적용한 ContextManager입니다.
워크플로우 데이터는 스냅샷만 유지하며, WorkflowManager가 진실의 원천입니다.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

# EventBus와 이벤트 타입 import
from python.workflow.v3.event_bus import event_bus
from python.workflow.v3.event_types import (
    EventType,
    create_project_event,
    create_context_event
)

logger = logging.getLogger(__name__)


class WorkflowSnapshot:
    """워크플로우 스냅샷 데이터"""
    def __init__(self):
        self.current_plan_id: Optional[str] = None
        self.current_plan_name: Optional[str] = None
        self.total_tasks: int = 0
        self.completed_tasks: int = 0
        self.progress_percent: float = 0.0
        self.status: str = "idle"
        self.last_updated: Optional[datetime] = None
        self.ttl_minutes: int = 30  # 캐시 유효 시간

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'current_plan_id': self.current_plan_id,
            'current_plan_name': self.current_plan_name,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'progress_percent': self.progress_percent,
            'status': self.status,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    def is_expired(self) -> bool:
        """캐시 만료 확인"""
        if not self.last_updated:
            return True

        expiry_time = self.last_updated + timedelta(minutes=self.ttl_minutes)
        return datetime.now() > expiry_time

    def update_from_event(self, event):
        """이벤트로부터 스냅샷 업데이트"""
        self.last_updated = datetime.now()

        if hasattr(event, 'payload'):
            payload = event.payload

            # 플랜 정보 업데이트
            if 'plan_id' in payload:
                self.current_plan_id = payload['plan_id']
            if 'plan_name' in payload:
                self.current_plan_name = payload['plan_name']
            if 'total_tasks' in payload:
                self.total_tasks = payload['total_tasks']
            if 'completed_tasks' in payload:
                self.completed_tasks = payload['completed_tasks']
            if 'plan_status' in payload:
                self.status = payload['plan_status']

            # 진행률 계산
            if self.total_tasks > 0:
                self.progress_percent = (self.completed_tasks / self.total_tasks) * 100
            else:
                self.progress_percent = 0.0


class ContextManager:
    """
    프로젝트 컨텍스트를 관리하는 중앙 매니저 (SSOT 적용)

    워크플로우 데이터는 스냅샷만 유지하며, 
    WorkflowManager가 진실의 원천입니다.
    """

    def __init__(self, base_path: str = "memory"):
        """ContextManager 초기화"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        # context.json만 사용 (workflow.json 제거)
        self.context_file = self.base_path / "context.json"

        self.current_project: Optional[str] = None
        self.context_data: Dict[str, Any] = {}
        self.workflow_snapshots: Dict[str, WorkflowSnapshot] = {}

        # 기존 컨텍스트 로드
        self._load_context()

        # 이벤트 핸들러 등록
        self._register_event_handlers()

        logger.info("ContextManager initialized with SSOT architecture")

    def _register_event_handlers(self):
        """이벤트 핸들러 등록"""
        # 워크플로우 관련 이벤트 구독
        event_bus.subscribe(EventType.PLAN_CREATED.value, self._on_plan_created)
        event_bus.subscribe(EventType.PLAN_UPDATED.value, self._on_plan_updated)
        event_bus.subscribe(EventType.PLAN_COMPLETED.value, self._on_plan_completed)
        event_bus.subscribe(EventType.PLAN_ARCHIVED.value, self._on_plan_archived)
        event_bus.subscribe(EventType.TASK_COMPLETED.value, self._on_task_completed)
        event_bus.subscribe(EventType.PROJECT_LOADED.value, self._on_project_loaded)

        logger.debug("Event handlers registered for workflow snapshots")

    def switch_project(self, new_project_name: str) -> bool:
        """
        프로젝트 전환 (이벤트 기반)
        """
        try:
            # 현재 프로젝트 저장
            if self.current_project:
                self.save_context()
                logger.info(f"Saved context for project: {self.current_project}")

            # 이전 프로젝트 기록
            previous_project = self.current_project

            # 새 프로젝트로 전환
            self.current_project = new_project_name

            # 새 프로젝트 컨텍스트 로드
            self._load_context()

            # 워크플로우 스냅샷 초기화
            if new_project_name not in self.workflow_snapshots:
                self.workflow_snapshots[new_project_name] = WorkflowSnapshot()

            # PROJECT_SWITCHED 이벤트 발행
            event = create_project_event(
                EventType.PROJECT_SWITCHED,
                project_name=new_project_name,
                previous_project=previous_project,
                timestamp=datetime.now().isoformat()
            )
            event_bus.publish(event)

            logger.info(f"Published PROJECT_SWITCHED event: {previous_project} -> {new_project_name}")

            return True

        except Exception as e:
            logger.error(f"Error switching project: {e}")
            return False

    def _on_project_loaded(self, event):
        """PROJECT_LOADED 이벤트 핸들러"""
        if hasattr(event, 'project_name') and event.project_name == self.current_project:
            logger.info(f"Project loaded confirmation received: {event.project_name}")

            # 초기 스냅샷 생성
            if self.current_project in self.workflow_snapshots:
                snapshot = self.workflow_snapshots[self.current_project]
                snapshot.update_from_event(event)

    def _on_plan_created(self, event):
        """PLAN_CREATED 이벤트 핸들러"""
        project_name = getattr(event, 'project_name', self.current_project)
        if project_name and project_name in self.workflow_snapshots:
            snapshot = self.workflow_snapshots[project_name]
            snapshot.update_from_event(event)
            snapshot.status = "active"
            logger.debug(f"Snapshot updated for plan creation: {snapshot.current_plan_name}")

    def _on_plan_updated(self, event):
        """PLAN_UPDATED 이벤트 핸들러"""
        project_name = getattr(event, 'project_name', self.current_project)
        if project_name and project_name in self.workflow_snapshots:
            snapshot = self.workflow_snapshots[project_name]
            snapshot.update_from_event(event)

    def _on_plan_completed(self, event):
        """PLAN_COMPLETED 이벤트 핸들러"""
        project_name = getattr(event, 'project_name', self.current_project)
        if project_name and project_name in self.workflow_snapshots:
            snapshot = self.workflow_snapshots[project_name]
            snapshot.status = "completed"
            snapshot.progress_percent = 100.0
            snapshot.last_updated = datetime.now()

    def _on_plan_archived(self, event):
        """PLAN_ARCHIVED 이벤트 핸들러"""
        project_name = getattr(event, 'project_name', self.current_project)
        if project_name and project_name in self.workflow_snapshots:
            # 스냅샷 초기화
            self.workflow_snapshots[project_name] = WorkflowSnapshot()
            logger.debug(f"Snapshot cleared for archived plan")

    def _on_task_completed(self, event):
        """TASK_COMPLETED 이벤트 핸들러"""
        project_name = getattr(event, 'project_name', self.current_project)
        if project_name and project_name in self.workflow_snapshots:
            snapshot = self.workflow_snapshots[project_name]

            # 완료된 태스크 수 증가
            if hasattr(event, 'payload') and 'completed_tasks' in event.payload:
                snapshot.completed_tasks = event.payload['completed_tasks']
            else:
                snapshot.completed_tasks += 1

            # 진행률 재계산
            if snapshot.total_tasks > 0:
                snapshot.progress_percent = (snapshot.completed_tasks / snapshot.total_tasks) * 100

            snapshot.last_updated = datetime.now()

    def get_workflow_snapshot(self, project_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        워크플로우 스냅샷 조회

        캐시가 만료되었거나 없으면 None 반환
        """
        project = project_name or self.current_project
        if not project or project not in self.workflow_snapshots:
            return None

        snapshot = self.workflow_snapshots[project]

        # 캐시 만료 확인
        if snapshot.is_expired():
            logger.debug(f"Workflow snapshot expired for project: {project}")
            return None

        return snapshot.to_dict()

    def _load_context(self):
        """컨텍스트 파일 로드 (workflow.json 제외)"""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    all_context = json.load(f)

                # 현재 프로젝트의 컨텍스트 로드
                if self.current_project and self.current_project in all_context:
                    self.context_data = all_context[self.current_project]
                else:
                    self.context_data = {}

                logger.debug(f"Loaded context for project: {self.current_project}")

            except Exception as e:
                logger.error(f"Error loading context: {e}")
                self.context_data = {}

    def save_context(self):
        """컨텍스트 저장 (스냅샷 포함)"""
        if not self.current_project:
            return

        try:
            # 전체 컨텍스트 로드
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    all_context = json.load(f)
            else:
                all_context = {}

            # 스냅샷 추가
            if self.current_project in self.workflow_snapshots:
                snapshot = self.workflow_snapshots[self.current_project]
                if not snapshot.is_expired():
                    self.context_data['workflow_snapshot'] = snapshot.to_dict()
                else:
                    # 만료된 스냅샷은 제거
                    self.context_data.pop('workflow_snapshot', None)

            # 현재 프로젝트 컨텍스트 업데이트
            all_context[self.current_project] = self.context_data

            # 저장
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(all_context, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved context for project: {self.current_project}")

            # CONTEXT_SAVED 이벤트 발행
            event = create_context_event(
                EventType.CONTEXT_SAVED,
                context_type="full_save",
                project_name=self.current_project,
                timestamp=datetime.now().isoformat()
            )
            event_bus.publish(event)

        except Exception as e:
            logger.error(f"Error saving context: {e}")

    def get_project_metadata(self, key: str, default: Any = None) -> Any:
        """프로젝트 메타데이터 조회"""
        return self.context_data.get(key, default)

    def set_project_metadata(self, key: str, value: Any):
        """프로젝트 메타데이터 설정"""
        self.context_data[key] = value
        self.save_context()

    def cleanup(self):
        """정리 작업 (이벤트 핸들러 제거)"""
        # 이벤트 핸들러 구독 해제
        event_bus.unsubscribe(EventType.PLAN_CREATED.value, self._on_plan_created)
        event_bus.unsubscribe(EventType.PLAN_UPDATED.value, self._on_plan_updated)
        event_bus.unsubscribe(EventType.PLAN_COMPLETED.value, self._on_plan_completed)
        event_bus.unsubscribe(EventType.PLAN_ARCHIVED.value, self._on_plan_archived)
        event_bus.unsubscribe(EventType.TASK_COMPLETED.value, self._on_task_completed)
        event_bus.unsubscribe(EventType.PROJECT_LOADED.value, self._on_project_loaded)

        # 마지막 저장
        self.save_context()

        logger.info("ContextManager cleanup completed")

    def migrate_legacy_data(self):
        """
        레거시 workflow.json 데이터 마이그레이션

        기존 workflow.json은 더 이상 사용하지 않으며,
        필요한 경우 WorkflowManager로 마이그레이션해야 합니다.
        """
        legacy_workflow_file = self.base_path / "workflow.json"

        if legacy_workflow_file.exists():
            logger.info("Legacy workflow.json found. Migration recommended.")

            # 백업 생성
            backup_file = self.base_path / f"workflow.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            legacy_workflow_file.rename(backup_file)
            logger.info(f"Legacy workflow.json backed up to: {backup_file}")
