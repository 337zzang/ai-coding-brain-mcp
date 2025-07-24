"""
Flow 비즈니스 로직 서비스
단순화된 3단계 상태 관리
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import logging

from ..domain.models import Flow, Plan, Task, TaskStatus, create_flow_id, create_plan_id, create_task_id
from ..repository.json_repository import JsonRepository
from ..exceptions import FlowError, ValidationError

logger = logging.getLogger(__name__)


class FlowService:
    """
    Flow 비즈니스 로직 서비스
    - 3단계 상태 관리 (TODO, DOING, DONE)
    - Context 자동 통합
    - 데이터 검증 및 변환
    """

    def __init__(self, 
                 repository: Optional[JsonRepository] = None,
                 context_enabled: bool = True):
        self._repo = repository or JsonRepository()
        self.context_enabled = context_enabled

        # 현재 선택된 항목
        self._current_flow_id: Optional[str] = None
        self._current_project: Optional[str] = None

        # 캐시 (메모리)
        self._flows: Dict[str, Flow] = {}
        self._load_all()

    def _load_all(self):
        """모든 Flow 로드"""
        try:
            data = self._repo.load()
            self._flows = {}

            for flow_id, flow_data in data.items():
                try:
                    if isinstance(flow_data, dict):
                        self._flows[flow_id] = Flow.from_dict(flow_data)
                except Exception as e:
                    logger.error(f"Failed to load flow {flow_id}: {e}")

        except Exception as e:
            logger.error(f"Failed to load flows: {e}")
            self._flows = {}

    def _persist(self):
        """변경사항 저장"""
        try:
            data = {fid: flow.to_dict() for fid, flow in self._flows.items()}
            return self._repo.save(data)
        except Exception as e:
            logger.error(f"Failed to persist flows: {e}")
            return False

    # === Flow 관리 ===

    def create_flow(self, name: str, project: Optional[str] = None) -> Flow:
        """Flow 생성"""
        if not name:
            raise ValidationError("Flow name is required")

        flow_id = create_flow_id(name)

        # 중복 체크
        if flow_id in self._flows:
            raise ValidationError(f"Flow '{flow_id}' already exists")

        flow = Flow(
            id=flow_id,
            name=name,
            project=project or self._current_project
        )

        self._flows[flow_id] = flow
        self._current_flow_id = flow_id

        if self._persist():
            logger.info(f"Created flow: {flow_id}")
            return flow
        else:
            # 롤백
            del self._flows[flow_id]
            raise FlowError("Failed to create flow")

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """Flow 조회"""
        return self._flows.get(flow_id)

    def list_flows(self, 
                   project: Optional[str] = None,
                   include_archived: bool = False) -> List[Flow]:
        """Flow 목록"""
        flows = list(self._flows.values())

        # 프로젝트 필터
        if project:
            flows = [f for f in flows if f.project == project]

        # 아카이브 필터
        if not include_archived:
            flows = [f for f in flows if not f.archived]

        # 정렬 (최신순)
        flows.sort(key=lambda f: f.created_at, reverse=True)

        return flows

    def delete_flow(self, flow_id: str) -> bool:
        """Flow 삭제"""
        if flow_id not in self._flows:
            return False

        # 현재 선택 해제
        if self._current_flow_id == flow_id:
            self._current_flow_id = None

        del self._flows[flow_id]

        if self._persist():
            logger.info(f"Deleted flow: {flow_id}")
            return True
        else:
            # 재로드 (롤백)
            self._load_all()
            return False

    def archive_flow(self, flow_id: str) -> bool:
        """Flow 아카이브"""
        flow = self.get_flow(flow_id)
        if not flow:
            return False

        flow.archive()

        if self._persist():
            logger.info(f"Archived flow: {flow_id}")
            return True
        else:
            return False

    # === Plan 관리 ===

    def add_plan(self, flow_id: str, name: str, description: str = "") -> Plan:
        """Plan 추가"""
        flow = self.get_flow(flow_id)
        if not flow:
            raise ValidationError(f"Flow '{flow_id}' not found")

        if not name:
            raise ValidationError("Plan name is required")

        plan = flow.add_plan(name, description)

        if self._persist():
            logger.info(f"Added plan: {plan.id} to flow: {flow_id}")
            return plan
        else:
            # 롤백
            del flow.plans[plan.id]
            raise FlowError("Failed to add plan")

    def get_plan(self, flow_id: str, plan_id: str) -> Optional[Plan]:
        """Plan 조회"""
        flow = self.get_flow(flow_id)
        if flow:
            return flow.plans.get(plan_id)
        return None

    def complete_plan(self, flow_id: str, plan_id: str) -> bool:
        """Plan 완료"""
        plan = self.get_plan(flow_id, plan_id)
        if not plan:
            return False

        plan.complete()

        if self._persist():
            logger.info(f"Completed plan: {plan_id}")
            return True
        else:
            return False

    # === Task 관리 ===

    def add_task(self, flow_id: str, plan_id: str, 
                 name: str, description: str = "") -> Task:
        """Task 추가"""
        plan = self.get_plan(flow_id, plan_id)
        if not plan:
            raise ValidationError(f"Plan '{plan_id}' not found")

        if not name:
            raise ValidationError("Task name is required")

        task = plan.add_task(name, description)

        if self._persist():
            logger.info(f"Added task: {task.id} to plan: {plan_id}")

            # Context 기록
            if self.context_enabled:
                task.add_action('created', {
                    'flow_id': flow_id,
                    'plan_id': plan_id
                })
                self._persist()

            return task
        else:
            # 롤백
            del plan.tasks[task.id]
            raise FlowError("Failed to add task")

    def get_task(self, flow_id: str, plan_id: str, task_id: str) -> Optional[Task]:
        """Task 조회"""
        plan = self.get_plan(flow_id, plan_id)
        if plan:
            return plan.tasks.get(task_id)
        return None

    def update_task_status(self, flow_id: str, plan_id: str, 
                          task_id: str, status: str) -> bool:
        """Task 상태 변경"""
        task = self.get_task(flow_id, plan_id, task_id)
        if not task:
            return False

        old_status = task.status

        # 레거시 상태 변환
        new_status = TaskStatus.from_legacy(status)

        if new_status == TaskStatus.DOING and old_status == TaskStatus.TODO:
            task.start()
        elif new_status == TaskStatus.DONE and old_status != TaskStatus.DONE:
            task.complete()
        else:
            task.status = new_status
            task.updated_at = datetime.now(timezone.utc).isoformat()

        if self._persist():
            logger.info(f"Updated task {task_id} status: {old_status} -> {new_status}")

            # Context 기록
            if self.context_enabled:
                task.add_action('status_changed', {
                    'from': old_status.value,
                    'to': new_status.value
                })
                self._persist()

            # Plan 자동 완료 체크
            self._check_plan_completion(flow_id, plan_id)

            return True
        else:
            return False

    def start_task(self, flow_id: str, plan_id: str, task_id: str) -> bool:
        """Task 시작"""
        return self.update_task_status(flow_id, plan_id, task_id, 'doing')

    def complete_task(self, flow_id: str, plan_id: str, 
                     task_id: str, message: str = "") -> bool:
        """Task 완료"""
        task = self.get_task(flow_id, plan_id, task_id)
        if not task:
            return False

        # 상태 변경
        success = self.update_task_status(flow_id, plan_id, task_id, 'done')

        if success and message:
            # 완료 메시지 기록
            task.add_action('completed', {'message': message})
            self._persist()

        return success

    def update_task_context(self, flow_id: str, plan_id: str, 
                           task_id: str, context_update: Dict[str, Any]) -> bool:
        """Task Context 업데이트"""
        task = self.get_task(flow_id, plan_id, task_id)
        if not task:
            return False

        # Context 병합
        task.context.update(context_update)
        task.updated_at = datetime.now(timezone.utc).isoformat()

        if self._persist():
            logger.info(f"Updated task {task_id} context")
            return True
        else:
            return False

    def add_task_action(self, flow_id: str, plan_id: str, 
                       task_id: str, action: str, data: Any = None) -> bool:
        """Task 액션 추가"""
        task = self.get_task(flow_id, plan_id, task_id)
        if not task:
            return False

        task.add_action(action, data)

        if self._persist():
            logger.info(f"Added action '{action}' to task {task_id}")
            return True
        else:
            return False

    # === 조회 기능 ===

    def list_plans(self, flow_id: str) -> List[Plan]:
        """Plan 목록"""
        flow = self.get_flow(flow_id)
        if flow:
            return list(flow.plans.values())
        return []

    def list_tasks(self, flow_id: str, plan_id: str) -> List[Task]:
        """Task 목록"""
        plan = self.get_plan(flow_id, plan_id)
        if plan:
            return list(plan.tasks.values())
        return []

    def get_all_tasks(self, flow_id: str) -> List[Tuple[str, Task]]:
        """Flow의 모든 Task (plan_id와 함께)"""
        flow = self.get_flow(flow_id)
        if not flow:
            return []

        tasks = []
        for plan_id, plan in flow.plans.items():
            for task in plan.tasks.values():
                tasks.append((plan_id, task))

        return tasks

    # === 현재 선택 관리 ===

    @property
    def current_flow(self) -> Optional[str]:
        """현재 선택된 Flow ID"""
        return self._current_flow_id

    @current_flow.setter
    def current_flow(self, flow_id: Optional[str]):
        """Flow 선택"""
        if flow_id and flow_id not in self._flows:
            raise ValidationError(f"Flow '{flow_id}' not found")
        self._current_flow_id = flow_id
        logger.info(f"Selected flow: {flow_id}")

    @property
    def current_project(self) -> Optional[str]:
        """현재 프로젝트"""
        return self._current_project

    @current_project.setter
    def current_project(self, project: Optional[str]):
        """프로젝트 설정"""
        self._current_project = project
        logger.info(f"Selected project: {project}")

    # === 유틸리티 ===

    def _check_plan_completion(self, flow_id: str, plan_id: str):
        """Plan 자동 완료 체크"""
        plan = self.get_plan(flow_id, plan_id)
        if not plan or plan.status == 'completed':
            return

        if plan.is_completed():
            plan.complete()
            self._persist()
            logger.info(f"Auto-completed plan: {plan_id}")

    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        total_flows = len(self._flows)
        active_flows = sum(1 for f in self._flows.values() if not f.archived)

        total_plans = 0
        total_tasks = 0
        task_by_status = {
            TaskStatus.TODO: 0,
            TaskStatus.DOING: 0,
            TaskStatus.DONE: 0
        }

        for flow in self._flows.values():
            total_plans += len(flow.plans)
            for plan in flow.plans.values():
                for task in plan.tasks.values():
                    total_tasks += 1
                    if task.status in task_by_status:
                        task_by_status[task.status] += 1

        return {
            'flows': {
                'total': total_flows,
                'active': active_flows,
                'archived': total_flows - active_flows
            },
            'plans': {
                'total': total_plans
            },
            'tasks': {
                'total': total_tasks,
                'todo': task_by_status[TaskStatus.TODO],
                'doing': task_by_status[TaskStatus.DOING],
                'done': task_by_status[TaskStatus.DONE]
            },
            'repository': self._repo.get_info()
        }

    def reload(self):
        """데이터 다시 로드"""
        self._load_all()
        logger.info("Reloaded all flows")
