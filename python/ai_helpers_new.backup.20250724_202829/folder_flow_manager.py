"""
폴더 기반 Flow Manager
- 프로젝트별 독립적인 Flow 관리
- 기존 API와 100% 호환
- 폴더 구조 기반 저장
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .service.folder_based_flow_service import FolderBasedFlowService
from .domain.models import Flow, Plan, Task, TaskStatus
from .decorators import auto_record
from .context_integration import ContextIntegration


class FolderFlowManager:
    """폴더 기반 Flow 관리자"""

    def __init__(self, project_path: Optional[str] = None, context_enabled: bool = True):
        """
        Args:
            project_path: 프로젝트 경로 (None이면 현재 디렉토리)
            context_enabled: Context 시스템 활성화 여부
        """
        # 프로젝트 경로 설정
        self.project_path = Path(project_path or os.getcwd())
        self.project_name = self.project_path.name

        # .ai-brain/flow 경로
        self.flow_base_path = self.project_path / '.ai-brain' / 'flow'

        # 서비스 초기화
        self._service = FolderBasedFlowService(str(self.flow_base_path))

        # Context 시스템
        self._context_enabled = context_enabled
        if context_enabled:
            self._context = ContextIntegration()

        # 현재 Flow ID (프로젝트당 하나)
        self._current_flow_id: Optional[str] = None

        # 초기화
        self._initialize()

    def _initialize(self):
        """초기화 - Flow 확인/생성"""
        # 디렉토리 생성
        self.flow_base_path.mkdir(parents=True, exist_ok=True)

        # 기존 Flow 찾기 (프로젝트당 하나)
        flows = self._service.list_flows(project=self.project_name)

        if flows:
            # 가장 최근 Flow 사용
            self._current_flow_id = flows[0].id
        else:
            # 새 Flow 생성
            flow = self._service.create_flow(
                name=self.project_name,
                project=self.project_name
            )
            self._current_flow_id = flow.id

    # --- Flow 관리 ---

    @property
    def current_flow(self) -> Optional[Flow]:
        """현재 활성 Flow"""
        if not self._current_flow_id:
            return None

        flow = self._service.load_flow(self._current_flow_id)

        # API 호환성: plan_ids를 plans 딕셔너리로 변환
        if flow and hasattr(flow, '_plan_ids'):
            # Lazy loading으로 plans 구성
            if not flow.plans:
                flow.plans = {}
                for plan_id in getattr(flow, '_plan_ids', []):
                    # 필요할 때만 로드
                    flow.plans[plan_id] = None  # 플레이스홀더

        return flow

    @auto_record
    def create_flow(self, name: str, project: Optional[str] = None) -> Flow:
        """새 Flow 생성 (API 호환성)"""
        # 폴더 기반에서는 프로젝트당 하나의 Flow만
        if project is None:
            project = self.project_name

        # 기존 Flow가 있으면 반환
        existing = self.current_flow
        if existing:
            return existing

        # 새 Flow 생성
        flow = self._service.create_flow(name, project)
        self._current_flow_id = flow.id

        return flow

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """Flow 조회"""
        return self._service.load_flow(flow_id)

    def list_flows(self) -> List[Flow]:
        """Flow 목록 (현재 프로젝트만)"""
        return self._service.list_flows(project=self.project_name)

    @auto_record
    def delete_flow(self, flow_id: str) -> bool:
        """Flow 삭제"""
        if flow_id == self._current_flow_id:
            self._current_flow_id = None

        self._service.delete_flow(flow_id)
        return True

    def select_flow(self, flow_id: str) -> Optional[Flow]:
        """Flow 선택"""
        flow = self._service.load_flow(flow_id)
        if flow:
            self._current_flow_id = flow_id
        return flow

    # --- Plan 관리 ---

    @auto_record
    def create_plan(self, flow_id: str, name: str) -> Plan:
        """Plan 생성"""
        # Plan ID 생성
        plan_id = self._generate_plan_id()

        # Plan 객체 생성
        plan = Plan(
            id=plan_id,
            name=name,
            tasks={},
            completed=False
        )

        # flow_id 설정
        plan.flow_id = flow_id

        # 서비스를 통해 저장
        self._service.create_plan(flow_id, plan_id, plan)

        # Flow의 plan_ids 업데이트
        flow = self._service.load_flow(flow_id)
        if flow:
            if not hasattr(flow, '_plan_ids'):
                flow._plan_ids = []
            flow._plan_ids.append(plan_id)
            flow.updated_at = datetime.now().isoformat()
            self._service.save_flow(flow)

        return plan

    def get_plan(self, flow_id: str, plan_id: str) -> Optional[Plan]:
        """Plan 조회"""
        return self._service.load_plan(flow_id, plan_id)

    def get_plans(self, flow_id: Optional[str] = None) -> List[Plan]:
        """Plan 목록 조회"""
        if flow_id is None:
            flow_id = self._current_flow_id

        if not flow_id:
            return []

        # Plan ID 목록 가져오기
        plan_ids = self._service.list_plan_ids(flow_id)

        # 각 Plan 로드
        plans = []
        for plan_id in plan_ids:
            plan = self._service.load_plan(flow_id, plan_id)
            if plan:
                plans.append(plan)

        return plans

    @auto_record
    def update_plan_status(self, flow_id: str, plan_id: str, completed: bool) -> None:
        """Plan 상태 업데이트"""
        plan = self._service.load_plan(flow_id, plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        plan.completed = completed
        plan.updated_at = datetime.now().isoformat()

        self._service.save_plan(plan)

    @auto_record
    def delete_plan(self, flow_id: str, plan_id: str) -> None:
        """Plan 삭제"""
        # Flow에서 plan_id 제거
        flow = self._service.load_flow(flow_id)
        if flow and hasattr(flow, '_plan_ids'):
            if plan_id in flow._plan_ids:
                flow._plan_ids.remove(plan_id)
                flow.updated_at = datetime.now().isoformat()
                self._service.save_flow(flow)

        # Plan 파일 삭제
        self._service.delete_plan(flow_id, plan_id)

    # --- Task 관리 ---

    @auto_record
    def create_task(self, flow_id: str, plan_id: str, name: str) -> Task:
        """Task 생성"""
        # Plan 로드
        plan = self._service.load_plan(flow_id, plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # Task ID 생성
        task_id = self._generate_task_id()

        # Task 객체 생성
        task = Task(
            id=task_id,
            name=name,
            status=TaskStatus.TODO.value
        )

        # Plan에 Task 추가
        plan.tasks[task_id] = task
        plan.updated_at = datetime.now().isoformat()

        # Plan 저장
        self._service.save_plan(plan)

        return task

    def get_task(self, flow_id: str, plan_id: str, task_id: str) -> Optional[Task]:
        """Task 조회"""
        plan = self._service.load_plan(flow_id, plan_id)
        if plan and task_id in plan.tasks:
            return plan.tasks[task_id]
        return None

    @auto_record
    def update_task_status(self, flow_id: str, plan_id: str, task_id: str, status: str) -> None:
        """Task 상태 업데이트"""
        plan = self._service.load_plan(flow_id, plan_id)
        if not plan or task_id not in plan.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = plan.tasks[task_id]
        task.status = status
        task.updated_at = datetime.now().isoformat()

        # 상태에 따른 시간 기록
        if status == TaskStatus.IN_PROGRESS.value and not task.started_at:
            task.started_at = datetime.now().isoformat()
        elif status == TaskStatus.DONE.value:
            task.completed_at = datetime.now().isoformat()

        # Plan 저장
        plan.updated_at = datetime.now().isoformat()
        self._service.save_plan(plan)

        # Plan 완료 여부 확인
        self._check_and_complete_plan(flow_id, plan_id)

    @auto_record
    def update_task_context(self, flow_id: str, plan_id: str, task_id: str, context: Dict[str, Any]) -> None:
        """Task 컨텍스트 업데이트"""
        plan = self._service.load_plan(flow_id, plan_id)
        if not plan or task_id not in plan.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = plan.tasks[task_id]
        task.context.update(context)
        task.updated_at = datetime.now().isoformat()

        # Plan 저장
        plan.updated_at = datetime.now().isoformat()
        self._service.save_plan(plan)

    @auto_record
    def delete_task(self, flow_id: str, plan_id: str, task_id: str) -> None:
        """Task 삭제"""
        plan = self._service.load_plan(flow_id, plan_id)
        if not plan or task_id not in plan.tasks:
            raise ValueError(f"Task {task_id} not found")

        # Task 제거
        del plan.tasks[task_id]
        plan.updated_at = datetime.now().isoformat()

        # Plan 저장
        self._service.save_plan(plan)

    def _check_and_complete_plan(self, flow_id: str, plan_id: str) -> None:
        """Plan의 모든 Task가 완료되었는지 확인"""
        plan = self._service.load_plan(flow_id, plan_id)
        if not plan:
            return

        # 모든 Task가 완료되었는지 확인
        all_done = all(
            task.status == TaskStatus.DONE.value 
            for task in plan.tasks.values()
        )

        if all_done and not plan.completed:
            plan.completed = True
            plan.updated_at = datetime.now().isoformat()
            self._service.save_plan(plan)

    # --- 유틸리티 메서드 ---

    def _generate_plan_id(self) -> str:
        """Plan ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d")
        # 오늘 날짜의 Plan 수 확인
        if self._current_flow_id:
            existing_plans = self._service.list_plan_ids(self._current_flow_id)
            today_plans = [p for p in existing_plans if p.startswith(f"plan_{timestamp}_")]
            seq = len(today_plans) + 1
        else:
            seq = 1

        return f"plan_{timestamp}_{seq:03d}"

    def _generate_task_id(self) -> str:
        """Task ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique = str(uuid.uuid4())[:6]
        return f"task_{timestamp}_{unique}"

    # --- 통계 및 관리 ---

    def get_stats(self) -> Dict[str, Any]:
        """전체 통계"""
        stats = {
            'project': self.project_name,
            'project_path': str(self.project_path),
            'current_flow_id': self._current_flow_id,
            'service_stats': self._service.get_stats()
        }

        if self._current_flow_id:
            flow = self.current_flow
            if flow:
                plan_count = len(self._service.list_plan_ids(flow.id))
                stats['flow_stats'] = {
                    'name': flow.name,
                    'plan_count': plan_count,
                    'created_at': flow.created_at,
                    'updated_at': flow.updated_at
                }

        return stats

    def clear_cache(self) -> None:
        """캐시 클리어"""
        self._service.clear_cache()
