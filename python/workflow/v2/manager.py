"""
Workflow v2 Manager - 성능 최적화 버전
"""
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager

from workflow.v2.models import WorkflowPlan, Task, TaskStatus, PlanStatus
from ai_helpers.helper_result import HelperResult
from workflow.v2.context_integration import get_context_integration


class WorkflowV2Manager:
    """워크플로우 v2 관리자 - 성능 최적화"""

    # 클래스 레벨 캐시
    _instance_cache: Dict[str, 'WorkflowV2Manager'] = {}

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.current_plan: Optional[WorkflowPlan] = None
        self.history: List[WorkflowPlan] = []
        self._dirty = False  # 변경사항 추적
        self._batch_mode = False  # 배치 모드

        # 워크플로우 파일 경로
        self.workflow_dir = os.path.join('memory', 'workflow_v2')
        os.makedirs(self.workflow_dir, exist_ok=True)
        self.workflow_file = os.path.join(self.workflow_dir, f'{project_name}_workflow.json')

        # 데이터 로드
        self.load_data()

    @classmethod
    def get_instance(cls, project_name: str) -> 'WorkflowV2Manager':
        """싱글톤 패턴으로 인스턴스 반환"""
        if project_name not in cls._instance_cache:
            cls._instance_cache[project_name] = cls(project_name)
        return cls._instance_cache[project_name]

    @contextmanager
    def batch_operations(self):
        """배치 모드 - 여러 작업을 한 번에 저장"""
        self._batch_mode = True
        self._dirty = False
        try:
            yield
        finally:
            self._batch_mode = False
            if self._dirty:
                self.save_data()

    def load_data(self):
        """저장된 워크플로우 데이터 로드"""
        if os.path.exists(self.workflow_file):
            try:
                with open(self.workflow_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 현재 플랜 로드
                if data.get('current_plan'):
                    self.current_plan = WorkflowPlan.from_dict(data['current_plan'])

                # 히스토리 로드
                self.history = [
                    WorkflowPlan.from_dict(plan_data) 
                    for plan_data in data.get('history', [])
                ]

                print(f"✅ v2 워크플로우 로드 완료: {self.project_name}")
            except Exception as e:
                print(f"⚠️ 워크플로우 로드 실패: {e}")

    def save_data(self) -> bool:
        """워크플로우 데이터를 파일에 저장"""
        if self._batch_mode:
            self._dirty = True
            return True

        try:
            data = {
                'current_plan': self.current_plan.to_dict() if self.current_plan else None,
                'history': [plan.to_dict() for plan in self.history]
            }

            # 원자적 쓰기를 위한 임시 파일 사용
            temp_file = self.workflow_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 원자적 교체
            os.replace(temp_file, self.workflow_file)

            print("💾 v2 워크플로우 저장 완료")

            # 컨텍스트 매니저와 동기화 (지연 import)
            try:
                from workflow.v2.context_integration import get_context_integration
                context_integration = get_context_integration()
                context_integration.sync_workflow_to_context(self.current_plan)
            except ImportError:
                pass  # 컨텍스트 통합이 없어도 계속 진행

            self._dirty = False
            return True
        except Exception as e:
            print(f"❌ v2 워크플로우 저장 실패: {e}")
            return False

    def create_plan(self, name: str, description: str = "") -> WorkflowPlan:
        """새로운 플랜 생성"""
        # 현재 플랜이 있으면 히스토리에 추가
        if self.current_plan and self.current_plan.status != PlanStatus.DRAFT:
            self.history.append(self.current_plan)

        # 새 플랜 생성
        self.current_plan = WorkflowPlan(name=name, description=description)
        self.save_data()

        return self.current_plan

    def add_task(self, title: str, description: str = "") -> Task:
        """현재 플랜에 태스크 추가"""
        if not self.current_plan:
            raise ValueError("활성 플랜이 없습니다")

        task = Task(title=title, description=description)
        self.current_plan.tasks.append(task)
        self.current_plan.updated_at = datetime.now().isoformat()

        self.save_data()
        return task

    def add_tasks_batch(self, tasks: List[Dict[str, str]]) -> List[Task]:
        """여러 태스크를 한 번에 추가 (성능 최적화)"""
        if not self.current_plan:
            raise ValueError("활성 플랜이 없습니다")

        added_tasks = []
        with self.batch_operations():
            for task_data in tasks:
                task = Task(
                    title=task_data.get('title', ''),
                    description=task_data.get('description', '')
                )
                self.current_plan.tasks.append(task)
                added_tasks.append(task)

            self.current_plan.updated_at = datetime.now().isoformat()

        return added_tasks

    def get_current_task(self) -> Optional[Task]:
        """현재 진행 중인 태스크 반환 (캐시됨)"""
        if not self.current_plan:
            return None

        # 간단한 캐싱
        if not hasattr(self, '_current_task_cache'):
            self._current_task_cache = None
            self._cache_time = None

        # 캐시 유효성 검사 (1초)
        import time
        current_time = time.time()
        if (self._current_task_cache is None or 
            self._cache_time is None or 
            current_time - self._cache_time > 1):

            for task in self.current_plan.tasks:
                if task.status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS]:
                    self._current_task_cache = task
                    self._cache_time = current_time
                    return task

            self._current_task_cache = None
            self._cache_time = current_time

        return self._current_task_cache

    def get_tasks(self) -> List[Task]:
        """현재 플랜의 모든 태스크 반환"""
        if not self.current_plan:
            return []
        return self.current_plan.tasks

    def complete_task(self, task_id: str, notes: str = "") -> Optional[Task]:
        """태스크 완료 처리"""
        if not self.current_plan:
            return None

        for task in self.current_plan.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                task.updated_at = task.completed_at
                if notes:
                    task.notes.append(notes)

                self.current_plan.updated_at = task.updated_at

                # 캐시 무효화
                if hasattr(self, '_current_task_cache'):
                    self._current_task_cache = None

                self.save_data()
                return task

        return None

    def get_status(self) -> Dict[str, Any]:
        """현재 워크플로우 상태 반환"""
        if not self.current_plan:
            return {
                'status': 'no_plan',
                'message': '활성 플랜이 없습니다'
            }

        total_tasks = len(self.current_plan.tasks)
        completed_tasks = sum(1 for t in self.current_plan.tasks if t.status == TaskStatus.COMPLETED)

        return {
            'status': 'active',
            'plan_name': self.current_plan.name,
            'plan_id': self.current_plan.id,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percent': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'current_task': self.get_current_task()
        }
