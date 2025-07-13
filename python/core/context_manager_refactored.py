"""
Context Manager - Event-Based Architecture
=========================================

이벤트 기반으로 리팩토링된 ContextManager입니다.
WorkflowManager와의 직접적인 결합을 제거하고 EventBus를 통해 통신합니다.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# EventBus와 이벤트 타입 import
from python.workflow.event_bus import event_bus
from python.workflow.event_types import (
    EventType,
    create_project_event,
    create_context_event
)

logger = logging.getLogger(__name__)


class ContextManager:
    """
    프로젝트 컨텍스트를 관리하는 중앙 매니저

    이벤트 기반 아키텍처로 리팩토링되어 다른 모듈과의 결합도가 낮아졌습니다.
    """

    def __init__(self, base_path: str = "memory"):
        """ContextManager 초기화"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        self.context_file = self.base_path / "context.json"
        self.workflow_file = self.base_path / "workflow.json"

        self.current_project: Optional[str] = None
        self.context_data: Dict[str, Any] = {}
        self.workflow_data: Dict[str, Any] = {}

        # 기존 컨텍스트 로드
        self._load_context()

        # 이벤트 핸들러 등록
        self._register_event_handlers()

        logger.info("ContextManager initialized with event-based architecture")

    def _register_event_handlers(self):
        """이벤트 핸들러 등록"""
        # 워크플로우 관련 이벤트 구독
        event_bus.subscribe(EventType.PLAN_CREATED.value, self._on_plan_created)
        event_bus.subscribe(EventType.PLAN_UPDATED.value, self._on_plan_updated)
        event_bus.subscribe(EventType.PLAN_COMPLETED.value, self._on_plan_completed)
        event_bus.subscribe(EventType.TASK_COMPLETED.value, self._on_task_completed)

        # 프로젝트 전환 완료 이벤트 구독
        event_bus.subscribe(EventType.PROJECT_LOADED.value, self._on_project_loaded)

        logger.debug("Event handlers registered")

    def switch_project(self, new_project_name: str) -> bool:
        """
        프로젝트 전환 (이벤트 기반)

        더 이상 WorkflowManager를 직접 호출하지 않고,
        PROJECT_SWITCHED 이벤트를 발행합니다.
        """
        try:
            # 현재 프로젝트 저장
            if self.current_project:
                self.save_all()
                logger.info(f"Saved context for project: {self.current_project}")

            # 이전 프로젝트 기록
            previous_project = self.current_project

            # 새 프로젝트로 전환
            self.current_project = new_project_name

            # 새 프로젝트 컨텍스트 로드
            self._load_context()

            # PROJECT_SWITCHED 이벤트 발행
            # WorkflowManager가 이 이벤트를 구독하여 자체적으로 전환을 처리합니다
            event = create_project_event(
                EventType.PROJECT_SWITCHED,
                project_name=new_project_name,
                previous_project=previous_project,
                timestamp=datetime.now().isoformat()
            )
            event_bus.publish(event)

            logger.info(f"Published PROJECT_SWITCHED event: {previous_project} -> {new_project_name}")

            # 컨텍스트 업데이트 이벤트도 발행
            context_event = create_context_event(
                EventType.CONTEXT_UPDATED,
                context_type="project_switch",
                project_name=new_project_name,
                context_data={
                    'previous_project': previous_project,
                    'switched_at': datetime.now().isoformat()
                }
            )
            event_bus.publish(context_event)

            return True

        except Exception as e:
            logger.error(f"Error switching project: {e}")
            return False

    def _on_project_loaded(self, event):
        """PROJECT_LOADED 이벤트 핸들러"""
        # WorkflowManager가 프로젝트 로드를 완료했을 때
        if hasattr(event, 'project_name') and event.project_name == self.current_project:
            logger.info(f"Project loaded confirmation received: {event.project_name}")

            # 워크플로우 정보가 있으면 업데이트
            if hasattr(event, 'payload') and 'workflow_info' in event.payload:
                self.workflow_data.update(event.payload['workflow_info'])
                self._save_workflow()

    def _on_plan_created(self, event):
        """PLAN_CREATED 이벤트 핸들러"""
        if hasattr(event, 'payload'):
            plan_info = {
                'plan_id': event.payload.get('plan_id'),
                'plan_name': event.payload.get('plan_name'),
                'created_at': event.timestamp.isoformat()
            }
            self.add_workflow_event({
                'type': 'plan_created',
                'data': plan_info,
                'timestamp': event.timestamp.isoformat()
            })
            logger.debug(f"Recorded plan creation: {plan_info['plan_name']}")

    def _on_plan_updated(self, event):
        """PLAN_UPDATED 이벤트 핸들러"""
        if hasattr(event, 'payload'):
            self.update_workflow_summary(event.payload)

    def _on_plan_completed(self, event):
        """PLAN_COMPLETED 이벤트 핸들러"""
        if hasattr(event, 'payload'):
            self.add_workflow_event({
                'type': 'plan_completed',
                'plan_id': event.payload.get('plan_id'),
                'timestamp': event.timestamp.isoformat()
            })

    def _on_task_completed(self, event):
        """TASK_COMPLETED 이벤트 핸들러"""
        if hasattr(event, 'payload'):
            task_info = {
                'task_id': event.payload.get('task_id'),
                'task_title': event.payload.get('task_title'),
                'completed_at': event.timestamp.isoformat()
            }
            self.add_workflow_event({
                'type': 'task_completed',
                'data': task_info,
                'timestamp': event.timestamp.isoformat()
            })

    def _load_context(self):
        """컨텍스트 파일 로드"""
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

        # 워크플로우 데이터도 로드
        self._load_workflow()

    def _load_workflow(self):
        """워크플로우 데이터 로드"""
        if self.workflow_file.exists():
            try:
                with open(self.workflow_file, 'r', encoding='utf-8') as f:
                    all_workflow = json.load(f)

                if self.current_project and self.current_project in all_workflow:
                    self.workflow_data = all_workflow[self.current_project]
                else:
                    self.workflow_data = {}

            except Exception as e:
                logger.error(f"Error loading workflow: {e}")
                self.workflow_data = {}

    def save_all(self):
        """모든 컨텍스트 데이터 저장"""
        self._save_context()
        self._save_workflow()

        # CONTEXT_SAVED 이벤트 발행
        event = create_context_event(
            EventType.CONTEXT_SAVED,
            context_type="full_save",
            project_name=self.current_project,
            timestamp=datetime.now().isoformat()
        )
        event_bus.publish(event)

    def _save_context(self):
        """컨텍스트 파일 저장"""
        if not self.current_project:
            return

        try:
            # 전체 컨텍스트 로드
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    all_context = json.load(f)
            else:
                all_context = {}

            # 현재 프로젝트 컨텍스트 업데이트
            all_context[self.current_project] = self.context_data

            # 저장
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(all_context, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved context for project: {self.current_project}")

        except Exception as e:
            logger.error(f"Error saving context: {e}")

    def _save_workflow(self):
        """워크플로우 데이터 저장"""
        if not self.current_project:
            return

        try:
            # 전체 워크플로우 데이터 로드
            if self.workflow_file.exists():
                with open(self.workflow_file, 'r', encoding='utf-8') as f:
                    all_workflow = json.load(f)
            else:
                all_workflow = {}

            # 현재 프로젝트 워크플로우 업데이트
            all_workflow[self.current_project] = self.workflow_data

            # 저장
            with open(self.workflow_file, 'w', encoding='utf-8') as f:
                json.dump(all_workflow, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving workflow: {e}")

    def update_workflow_summary(self, summary: Dict[str, Any]):
        """워크플로우 요약 정보 업데이트"""
        if 'workflow_summary' not in self.workflow_data:
            self.workflow_data['workflow_summary'] = {}

        self.workflow_data['workflow_summary'].update(summary)
        self.workflow_data['last_updated'] = datetime.now().isoformat()

        self._save_workflow()

    def add_workflow_event(self, event: Dict[str, Any]):
        """워크플로우 이벤트 추가"""
        if 'events' not in self.workflow_data:
            self.workflow_data['events'] = []

        self.workflow_data['events'].append(event)

        # 최대 100개까지만 유지
        if len(self.workflow_data['events']) > 100:
            self.workflow_data['events'] = self.workflow_data['events'][-100:]

        self._save_workflow()

    def get_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 태스크의 컨텍스트 조회"""
        task_contexts = self.context_data.get('task_contexts', {})
        return task_contexts.get(task_id)

    def clear_workflow_data(self):
        """워크플로우 데이터 초기화"""
        self.workflow_data = {}
        self._save_workflow()

    def get_recent_workflow_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 워크플로우 이벤트 조회"""
        events = self.workflow_data.get('events', [])
        return events[-limit:] if events else []

    def cleanup(self):
        """정리 작업 (이벤트 핸들러 제거)"""
        # 이벤트 핸들러 구독 해제
        event_bus.unsubscribe(EventType.PLAN_CREATED.value, self._on_plan_created)
        event_bus.unsubscribe(EventType.PLAN_UPDATED.value, self._on_plan_updated)
        event_bus.unsubscribe(EventType.PLAN_COMPLETED.value, self._on_plan_completed)
        event_bus.unsubscribe(EventType.TASK_COMPLETED.value, self._on_task_completed)
        event_bus.unsubscribe(EventType.PROJECT_LOADED.value, self._on_project_loaded)

        # 마지막 저장
        self.save_all()

        logger.info("ContextManager cleanup completed")
