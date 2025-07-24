# flow_manager.py
'''
단순화된 Flow Manager
Phase 2 구조 개선 - 계층 단순화
'''

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import threading

from .service.cached_flow_service import CachedFlowService
from .domain.models import Flow, Plan, Task, TaskStatus, create_flow_id, create_plan_id, create_task_id
from .exceptions import FlowError, ValidationError
from .context_integration import ContextIntegration
from .flow_context_wrapper import record_flow_action, record_plan_action, record_task_action
from .decorators import auto_record


class FlowManager:
    """
    단순화된 Flow Manager
    - 직접적인 비즈니스 로직 처리
    - CachedFlowService를 통한 저장소 접근
    - Context 자동 통합
    """

    def __init__(self, base_path: str = '.ai-brain', context_enabled: bool = True):
        self._service = CachedFlowService(base_path)
        self._context_enabled = context_enabled
        self._current_flow_id: Optional[str] = None
        self._current_project: Optional[str] = None
        self._lock = threading.RLock()

        # Context 통합
        if self._context_enabled:
            self._context = ContextIntegration()

    # === Flow 관리 ===

    @auto_record(capture_result=True)
    def create_flow(self, name: str, project: Optional[str] = None) -> Flow:
        """Flow 생성"""
        flow_id = create_flow_id()
        flow = Flow(
            id=flow_id,
            name=name,
            plans={},
            project=project or self._current_project
        )

        self._service.save_flow(flow)
        self._current_flow_id = flow_id

        # Context 기록
        if self._context_enabled:
            record_flow_action(flow_id, 'flow_created', {
                'name': name,
                'project': flow.project
            })

        return flow

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """Flow 조회"""
        return self._service.get_flow(flow_id)

    def list_flows(self, project: Optional[str] = None) -> List[Flow]:
        """Flow 목록 조회"""
        flows = self._service.list_flows()

        # 프로젝트 필터링
        if project:
            flows = [f for f in flows if f.project == project]

        return flows

    @auto_record(capture_result=True)
    def delete_flow(self, flow_id: str):
        """Flow 삭제"""
        # 현재 CachedFlowService는 개별 삭제를 지원하지 않으므로
        # 전체를 다시 저장하는 방식으로 구현
        from pathlib import Path
        import json

        flows_file = Path(self._service.base_path) / 'flows.json'

        if flows_file.exists():
            # 전체 flows 로드
            with open(flows_file, 'r', encoding='utf-8') as f:
                all_flows = json.load(f)

            # 해당 Flow 삭제
            if flow_id in all_flows:
                del all_flows[flow_id]

                # 다시 저장
                with open(flows_file, 'w', encoding='utf-8') as f:
                    json.dump(all_flows, f, ensure_ascii=False, indent=2)

                # 캐시 무효화
                self._service._cache.invalidate(flow_id)

        if self._current_flow_id == flow_id:
            self._current_flow_id = None

        # Context 기록
        if self._context_enabled:
            record_flow_action(flow_id, 'flow_deleted', {})

    @property
    def current_flow(self) -> Optional[Flow]:
        """현재 Flow"""
        if self._current_flow_id:
            return self.get_flow(self._current_flow_id)
        return None

    @current_flow.setter
    def current_flow(self, flow_id: str):
        """현재 Flow 설정"""
        if flow_id and self.get_flow(flow_id):
            self._current_flow_id = flow_id
        else:
            raise ValidationError(f"Flow를 찾을 수 없음: {flow_id}")

    # === Project 관리 ===
    def get_project(self) -> Optional[str]:
        """현재 프로젝트 반환"""
        return self._current_project

    def set_project(self, project: str) -> None:
        """프로젝트 설정"""
        with self._lock:
            self._current_project = project
            if self._context_enabled:
                self._context.record_flow_action(
                    "system",
                    "project_changed",
                    {'project': project}
                )

    @auto_record(capture_result=True)
    def select_flow(self, flow_id: str) -> bool:
        """Flow 선택"""
        with self._lock:
            flow = self.get_flow(flow_id)
            if flow:
                self._current_flow_id = flow_id
                if self._context_enabled:
                    self._context.record_flow_action(
                        flow_id,
                        "flow_selected",
                        {'flow_name': flow.name}
                    )
                return True
            return False

    # === Plan 관리 ===

    @auto_record(capture_result=True)
    def create_plan(self, flow_id: str, name: str) -> Plan:
        """Plan 생성"""
        flow = self.get_flow(flow_id)
        if not flow:
            raise ValidationError(f"Flow를 찾을 수 없음: {flow_id}")

        plan_id = create_plan_id()
        plan = Plan(
            id=plan_id,
            name=name,
            tasks={}
        )

        # Flow에 Plan 추가
        flow.plans[plan_id] = plan
        flow.updated_at = datetime.now(timezone.utc).isoformat()

        self._service.save_flow(flow)

        # Context 기록
        if self._context_enabled:
            record_plan_action(flow_id, plan_id, 'plan_created', {
                'name': name
            })

        return plan

    @auto_record(capture_result=False)
    def update_plan_status(self, flow_id: str, plan_id: str, completed: bool):
        """Plan 완료 상태 업데이트"""
        flow = self.get_flow(flow_id)
        if not flow or plan_id not in flow.plans:
            raise ValidationError(f"Plan을 찾을 수 없음: {plan_id}")

        plan = flow.plans[plan_id]
        plan.completed = completed
        plan.updated_at = datetime.now(timezone.utc).isoformat()

        self._service.save_flow(flow)

        # Context 기록
        if self._context_enabled:
            record_plan_action(flow_id, plan_id, 'plan_status_updated', {
                'completed': completed
            })

    def delete_plan(self, flow_id: str, plan_id: str):
        """Plan 삭제"""
        flow = self.get_flow(flow_id)
        if not flow or plan_id not in flow.plans:
            raise ValidationError(f"Plan을 찾을 수 없음: {plan_id}")

        del flow.plans[plan_id]
        flow.updated_at = datetime.now(timezone.utc).isoformat()

        self._service.save_flow(flow)

        # Context 기록
        if self._context_enabled:
            record_plan_action(flow_id, plan_id, 'plan_deleted', {})

    # === Task 관리 ===

    @auto_record(capture_result=True)
    def create_task(self, flow_id: str, plan_id: str, name: str) -> Task:
        """Task 생성"""
        flow = self.get_flow(flow_id)
        if not flow or plan_id not in flow.plans:
            raise ValidationError(f"Plan을 찾을 수 없음: {plan_id}")

        task_id = create_task_id()
        task = Task(
            id=task_id,
            name=name,
            status=TaskStatus.TODO.value
        )

        plan = flow.plans[plan_id]
        plan.tasks[task_id] = task
        plan.updated_at = datetime.now(timezone.utc).isoformat()
        flow.updated_at = datetime.now(timezone.utc).isoformat()

        self._service.save_flow(flow)

        # Context 기록
        if self._context_enabled:
            record_task_action(flow_id, task_id, 'task_created', {
                'name': name,
                'plan_id': plan_id
            })

        return task

    @auto_record(capture_result=False)
    def update_task_status(self, flow_id: str, plan_id: str, task_id: str, status: str):
        """Task 상태 업데이트"""
        # 상태 검증
        if status not in [s.value for s in TaskStatus]:
            raise ValidationError(f"유효하지 않은 상태: {status}")

        # CachedFlowService의 최적화된 메서드 사용
        self._service.update_task_status(flow_id, plan_id, task_id, status)

        # Context 기록
        if self._context_enabled:
            record_task_action(flow_id, task_id, 'task_status_updated', {
                'status': status,
                'plan_id': plan_id
            })

        # Plan 자동 완료 체크
        self._check_and_complete_plan(flow_id, plan_id)

    def update_task_context(self, flow_id: str, plan_id: str, task_id: str, context: Dict[str, Any]):
        """Task context 업데이트"""
        flow = self.get_flow(flow_id)
        if not flow or plan_id not in flow.plans or task_id not in flow.plans[plan_id].tasks:
            raise ValidationError(f"Task를 찾을 수 없음: {task_id}")

        task = flow.plans[plan_id].tasks[task_id]
        task.context.update(context)
        task.updated_at = datetime.now(timezone.utc).isoformat()

        self._service.save_flow(flow)

        # Context 기록
        if self._context_enabled:
            record_task_action(flow_id, task_id, 'task_context_updated', context)

    @auto_record(capture_result=True)
    def delete_task(self, flow_id: str, plan_id: str, task_id: str):
        """Task 삭제"""
        flow = self.get_flow(flow_id)
        if not flow or plan_id not in flow.plans or task_id not in flow.plans[plan_id].tasks:
            raise ValidationError(f"Task를 찾을 수 없음: {task_id}")

        del flow.plans[plan_id].tasks[task_id]
        flow.plans[plan_id].updated_at = datetime.now(timezone.utc).isoformat()
        flow.updated_at = datetime.now(timezone.utc).isoformat()

        self._service.save_flow(flow)

        # Context 기록
        if self._context_enabled:
            record_task_action(flow_id, task_id, 'task_deleted', {
                'plan_id': plan_id
            })

    # === 헬퍼 메서드 ===

    def _check_and_complete_plan(self, flow_id: str, plan_id: str):
        """Plan의 모든 Task가 완료되었는지 확인하고 자동 완료"""
        flow = self.get_flow(flow_id)
        if not flow or plan_id not in flow.plans:
            return

        plan = flow.plans[plan_id]
        if plan.completed:
            return  # 이미 완료됨

        # 모든 Task가 completed 또는 reviewing 상태인지 확인
        all_tasks = list(plan.tasks.values())
        if not all_tasks:
            return  # Task가 없으면 자동 완료하지 않음

        completed_tasks = [t for t in all_tasks if t.status in ['completed', 'reviewing']]

        if len(completed_tasks) == len(all_tasks):
            # 모든 Task 완료 - Plan 자동 완료
            self.update_plan_status(flow_id, plan_id, True)

            # Context에 자동 완료 기록
            if self._context_enabled:
                record_plan_action(flow_id, plan_id, 'plan_auto_completed', {
                    'total_tasks': len(all_tasks),
                    'trigger': 'all_tasks_completed'
                })

            print(f"🎉 Plan '{plan.name}'의 모든 Task가 완료되어 Plan이 자동으로 완료되었습니다!")

    # === 프로젝트 관리 ===

    @property
    def current_project(self) -> Optional[str]:
        """현재 프로젝트"""
        return self._current_project

    @current_project.setter
    def current_project(self, project: str):
        """현재 프로젝트 설정"""
        self._current_project = project

    # === 통계 ===

    def get_statistics(self) -> Dict[str, Any]:
        """전체 통계"""
        flows = self.list_flows()

        total_plans = 0
        total_tasks = 0
        completed_tasks = 0

        for flow in flows:
            total_plans += len(flow.plans)
            for plan in flow.plans.values():
                total_tasks += len(plan.tasks)
                completed_tasks += sum(1 for t in plan.tasks.values() 
                                     if t.status in ['completed', 'reviewing'])

        return {
            'total_flows': len(flows),
            'total_plans': total_plans,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': completed_tasks / total_tasks if total_tasks > 0 else 0
        }


    @auto_record(capture_result=True)
    def get_plans(self, flow_id: str = None) -> List[Plan]:
        """Flow의 모든 Plan 반환

        Args:
            flow_id: Flow ID (None이면 현재 Flow 사용)

        Returns:
            Plan 객체 리스트
        """
        if flow_id is None:
            flow_id = self._current_flow_id

        flow = self.get_flow(flow_id)
        return list(flow.plans.values()) if flow else []

    @auto_record(capture_result=True)
    def get_tasks(self, flow_id: str, plan_id: str) -> List[Task]:
        """Plan의 모든 Task 반환

        Args:
            flow_id: Flow ID
            plan_id: Plan ID

        Returns:
            Task 객체 리스트
        """
        flow = self.get_flow(flow_id)
        if flow and plan_id in flow.plans:
            return list(flow.plans[plan_id].tasks.values())
        return []

    def get_current_flow(self) -> Optional[Flow]:
        """현재 선택된 Flow 반환

        Returns:
            현재 Flow 객체 또는 None
        """
        if self._current_flow_id:
            return self.get_flow(self._current_flow_id)
        return None

    @auto_record(capture_result=False)
    def complete_task(self, flow_id: str, plan_id: str, task_id: str) -> bool:
        """Task를 완료 상태로 변경

        Args:
            flow_id: Flow ID
            plan_id: Plan ID
            task_id: Task ID

        Returns:
            성공 여부
        """
        # Task 완료 처리
        self.update_task_status(flow_id, plan_id, task_id, 'completed')

        # Plan의 모든 Task가 완료되었는지 확인
        tasks = self.get_tasks(flow_id, plan_id)
        if tasks and all(t.status.value == 'completed' for t in tasks):
            self.update_plan_status(flow_id, plan_id, 'completed')

        return True

    @auto_record(capture_result=True)
    def add_note(self, flow_id: str, note: str, plan_id: str = None, task_id: str = None) -> bool:
        """Flow, Plan 또는 Task에 메모 추가

        Args:
            flow_id: Flow ID
            note: 메모 내용
            plan_id: Plan ID (선택)
            task_id: Task ID (선택)

        Returns:
            성공 여부
        """
        flow = self.get_flow(flow_id)
        if not flow:
            return False

        timestamp = datetime.now().isoformat()
        note_entry = {'timestamp': timestamp, 'note': note}

        if task_id and plan_id:
            # Task에 메모 추가
            if plan_id in flow.plans and task_id in flow.plans[plan_id].tasks:
                task = flow.plans[plan_id].tasks[task_id]
                if not hasattr(task, 'notes'):
                    task.notes = []
                task.notes.append(note_entry)
        elif plan_id:
            # Plan에 메모 추가
            if plan_id in flow.plans:
                plan = flow.plans[plan_id]
                if not hasattr(plan, 'notes'):
                    plan.notes = []
                plan.notes.append(note_entry)
        else:
            # Flow에 메모 추가
            if not hasattr(flow, 'notes'):
                flow.notes = []
            flow.notes.append(note_entry)

        self._service.save_flow(flow)

        # Context 기록
        if self._context_enabled:
            self._context.record_flow_action(
                flow_id, 'note_added',
                {
                    'plan_id': plan_id,
                    'task_id': task_id,
                    'note_preview': note[:50] + '...' if len(note) > 50 else note
                }
            )

        return True

    @auto_record(capture_result=True)
    def batch_update(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """여러 Task를 일괄 업데이트

        Args:
            updates: 업데이트 정보 리스트
                    [{'flow_id': '', 'plan_id': '', 'task_id': '', 'status': ''}, ...]

        Returns:
            처리 결과 {'success': n, 'failed': n, 'errors': [...]}
        """
        results = {'success': 0, 'failed': 0, 'errors': []}

        for update in updates:
            try:
                flow_id = update.get('flow_id')
                plan_id = update.get('plan_id')
                task_id = update.get('task_id')
                status = update.get('status')

                if flow_id and plan_id and task_id and status:
                    self.update_task_status(flow_id, plan_id, task_id, status)
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Invalid update: {update}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))

        return results