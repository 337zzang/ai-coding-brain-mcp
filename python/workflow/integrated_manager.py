"""
Integrated Workflow Manager with Stdout Protocol v3.0
워크플로우 시스템과 프로토콜을 통합한 개선된 매니저
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

# Stdout Protocol import
try:
    from ai_helpers.protocols import (
        get_protocol, get_id_generator, get_tracker,
        StdoutProtocol, ExecutionTracker, IDGenerator
    )
    PROTOCOL_AVAILABLE = True
except ImportError:
    PROTOCOL_AVAILABLE = False
    print("⚠️ Stdout Protocol not available, falling back to basic mode")

from .models import Task, Plan, TaskStatus, PlanStatus

class IntegratedWorkflowManager:
    """프로토콜 통합 워크플로우 매니저"""

    def __init__(self, base_dir: str = "memory"):
        self.base_dir = Path(base_dir)
        self.workflow_dir = self.base_dir / "workflow_data"
        self.workflow_dir.mkdir(parents=True, exist_ok=True)

        # Protocol 초기화
        if PROTOCOL_AVAILABLE:
            self.protocol = get_protocol()
            self.id_gen = get_id_generator()
            self.tracker = get_tracker()
        else:
            self.protocol = None
            self.id_gen = None
            self.tracker = None

        # 워크플로우 파일 경로
        self.current_workflow_file = self.base_dir / "current_workflow.json"
        self.workflow_events_file = self.base_dir / "workflow_events.json"

        self._ensure_structure()

        # 시작 시 프로토콜 섹션 생성
        if self.protocol:
            self.session_id = self.protocol.section("workflow_session")
            self.protocol.data("manager_initialized", datetime.now().isoformat())

    def __del__(self):
        """소멸자에서 섹션 종료"""
        if hasattr(self, 'protocol') and self.protocol and hasattr(self, 'session_id'):
            self.protocol.end_section()

    @property
    def _tracked(self):
        """프로토콜 추적 데코레이터"""
        if self.tracker:
            return self.tracker.track
        else:
            # 프로토콜이 없으면 그냥 함수 반환
            return lambda f: f

    def _ensure_structure(self):
        """필요한 파일 구조 확인 및 생성"""
        if not self.current_workflow_file.exists():
            self._save_workflow_file({
                "active": False,
                "plan_id": None,
                "created_at": datetime.now().isoformat()
            })

        if not self.workflow_events_file.exists():
            with open(self.workflow_events_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _save_workflow_file(self, data: dict):
        """워크플로우 파일 저장 (프로토콜 통합)"""
        if self.protocol:
            # 체크포인트로 저장
            ckpt_id = self.protocol.checkpoint("workflow_state", data)
            data['checkpoint_id'] = ckpt_id
            self.protocol.data("workflow_saved", ckpt_id)

        with open(self.current_workflow_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_workflow_file(self) -> dict:
        """워크플로우 파일 로드"""
        with open(self.current_workflow_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if self.protocol and 'checkpoint_id' in data:
            self.protocol.data("workflow_loaded", data['checkpoint_id'])

        return data

    def _log_event(self, event_type: str, data: dict):
        """이벤트 로깅 (프로토콜 통합)"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # 프로토콜로도 기록
        if self.protocol:
            event_id = self.protocol.data(f"workflow_event_{event_type}", json.dumps(data))
            event['protocol_id'] = event_id

        # 파일에 저장
        events = []
        if self.workflow_events_file.exists():
            with open(self.workflow_events_file, 'r', encoding='utf-8') as f:
                events = json.load(f)

        events.append(event)

        with open(self.workflow_events_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)

    @_tracked
    def create_plan(self, name: str, description: str = "") -> Plan:
        """새 작업 계획 생성 (프로토콜 추적)"""
        if self.protocol:
            section_id = self.protocol.section(f"create_plan_{name}")

        plan = Plan(name=name, description=description)

        # 계획 파일 저장
        plan_file = self.workflow_dir / f"plan_{plan.id}.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)

        # 현재 워크플로우 업데이트
        workflow_data = {
            "active": True,
            "plan_id": plan.id,
            "plan_name": plan.name,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at
        }
        self._save_workflow_file(workflow_data)

        # 이벤트 로깅
        self._log_event("plan_created", {
            "plan_id": plan.id,
            "name": plan.name
        })

        if self.protocol:
            self.protocol.data("plan_created", plan.id)
            self.protocol.end_section()

        return plan

    @_tracked
    def add_task(self, plan_id: str, title: str, description: str = "") -> Task:
        """계획에 작업 추가 (프로토콜 추적)"""
        if self.protocol:
            section_id = self.protocol.section(f"add_task_{title}")

        # 계획 로드
        plan = self._get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # 작업 생성
        task = Task(
            title=title,
            description=description,
            order=len(plan.tasks) + 1
        )

        # 계획에 추가
        plan.add_task(task)

        # 저장
        plan_file = self.workflow_dir / f"plan_{plan.id}.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)

        # 이벤트 로깅
        self._log_event("task_added", {
            "plan_id": plan_id,
            "task_id": task.id,
            "title": task.title
        })

        if self.protocol:
            self.protocol.data("task_added", task.id)
            self.protocol.progress(len(plan.tasks), plan.total_tasks or len(plan.tasks), "tasks_defined")
            self.protocol.end_section()

        return task

    @_tracked
    def start_task(self, task_id: str) -> bool:
        """작업 시작 (프로토콜 섹션 생성)"""
        workflow = self._load_workflow_file()
        if not workflow.get('active'):
            return False

        plan = self._get_plan(workflow['plan_id'])
        if not plan:
            return False

        task = self._find_task(plan, task_id)
        if not task:
            return False

        # 프로토콜 섹션 시작 (작업별 섹션)
        if self.protocol:
            task_section_id = self.protocol.section(f"task_{task_id}_{task.title}")
            task.metadata['protocol_section_id'] = task_section_id
            self.protocol.data("task_started", task.title)

        # 작업 시작
        task.start()

        # 현재 작업 업데이트
        workflow['current_task'] = task.to_dict()
        self._save_workflow_file(workflow)

        # 계획 저장
        plan_file = self.workflow_dir / f"plan_{plan.id}.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)

        # 이벤트 로깅
        self._log_event("task_started", {
            "plan_id": plan.id,
            "task_id": task.id,
            "title": task.title
        })

        return True

    @_tracked
    def complete_task(self, task_id: str, notes: str = "") -> bool:
        """작업 완료 (프로토콜 섹션 종료)"""
        workflow = self._load_workflow_file()
        if not workflow.get('active'):
            return False

        plan = self._get_plan(workflow['plan_id'])
        if not plan:
            return False

        task = self._find_task(plan, task_id)
        if not task:
            return False

        # 작업 완료
        task.complete(notes)

        # 프로토콜 섹션 종료
        if self.protocol and 'protocol_section_id' in task.metadata:
            self.protocol.data("task_completed", task.title)
            self.protocol.end_section()  # 작업 섹션 종료

        # 진행률 업데이트
        completed = len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED])
        total = len(plan.tasks)

        if self.protocol:
            self.protocol.progress(completed, total, f"plan_{plan.id}")

        # 워크플로우 업데이트
        workflow['completed_tasks'] = completed
        workflow['total_tasks'] = total
        workflow['current_task'] = None

        # 모든 작업 완료 시 계획 완료
        if completed == total:
            plan.complete()
            workflow['active'] = False
            if self.protocol:
                self.protocol.data("plan_completed", plan.id)

        self._save_workflow_file(workflow)

        # 계획 저장
        plan_file = self.workflow_dir / f"plan_{plan.id}.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)

        # 이벤트 로깅
        self._log_event("task_completed", {
            "plan_id": plan.id,
            "task_id": task.id,
            "title": task.title,
            "notes": notes
        })

        return True

    def get_status(self) -> dict:
        """현재 워크플로우 상태 조회"""
        workflow = self._load_workflow_file()

        if not workflow.get('active'):
            return {
                "active": False,
                "message": "No active workflow"
            }

        plan = self._get_plan(workflow['plan_id'])
        if not plan:
            return {
                "active": False,
                "message": "Plan not found"
            }

        completed = len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED])
        pending = len([t for t in plan.tasks if t.status == TaskStatus.PENDING])
        in_progress = len([t for t in plan.tasks if t.status == TaskStatus.IN_PROGRESS])

        status = {
            "active": True,
            "plan_id": plan.id,
            "plan_name": plan.name,
            "total_tasks": len(plan.tasks),
            "completed_tasks": completed,
            "pending_tasks": pending,
            "in_progress_tasks": in_progress,
            "progress_percentage": (completed / len(plan.tasks) * 100) if plan.tasks else 0,
            "current_task": workflow.get('current_task'),
            "created_at": plan.created_at,
            "updated_at": plan.updated_at
        }

        # 프로토콜 정보 추가
        if self.protocol and hasattr(self, 'session_id'):
            status['protocol_session_id'] = self.session_id
            status['protocol_enabled'] = True
        else:
            status['protocol_enabled'] = False

        return status

    def _get_plan(self, plan_id: str) -> Optional[Plan]:
        """계획 로드"""
        plan_file = self.workflow_dir / f"plan_{plan_id}.json"
        if not plan_file.exists():
            return None

        with open(plan_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return Plan.from_dict(data)

    def _find_task(self, plan: Plan, task_id: str) -> Optional[Task]:
        """작업 찾기"""
        for task in plan.tasks:
            if task.id == task_id:
                return task
        return None
