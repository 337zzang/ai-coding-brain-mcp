"""Flow 일괄 작업 기능"""
import json
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime
from .flow_context_wrapper import record_flow_action, record_task_action, record_plan_action
from .domain.models import TaskStatus

class FlowBatchProcessor:
    """Flow 일괄 작업 처리기"""

    def __init__(self, flows_file: str = ".ai-brain/flows.json"):
        self.flows_file = flows_file
        self.dry_run = False  # 실제 실행 없이 결과만 미리보기
        self.batch_log = []

    def set_dry_run(self, dry_run: bool = True):
        """Dry run 모드 설정"""
        self.dry_run = dry_run
        return self

    def _load_flows(self) -> Dict[str, Any]:
        """Flow 데이터 로드"""
        with open(self.flows_file, 'r') as f:
            return json.load(f)

    def _save_flows(self, data: Dict[str, Any]):
        """Flow 데이터 저장"""
        if not self.dry_run:
            with open(self.flows_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

    def _log_action(self, action: str, target: str, details: Dict[str, Any]):
        """작업 로그 기록"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'details': details,
            'dry_run': self.dry_run
        }
        self.batch_log.append(log_entry)

    def batch_update_task_status(self, 
                                task_filter: Callable[[Dict[str, Any]], bool],
                                new_status: str) -> Tuple[int, List[Dict[str, Any]]]:
        """일괄 Task 상태 변경

        Args:
            task_filter: Task 필터 함수
            new_status: 새로운 상태

        Returns:
            (변경된 Task 수, 변경 상세 리스트)
        """
        data = self._load_flows()
        updated_count = 0
        updates = []

        for flow_id, flow in data.get('flows', {}).items():
            for plan_id, plan in flow.get('plans', {}).items():
                for task_id, task in plan.get('tasks', {}).items():
                    if task_filter(task):
                        old_status = task.get('status')

                        if not self.dry_run:
                            task['status'] = new_status
                            task['updated_at'] = datetime.now().isoformat()

                            # Context 기록
                            record_task_action(flow_id, task_id, 'batch_status_update', {
                                'old_status': old_status,
                                'new_status': new_status,
                                'task_name': task.get('name')
                            })

                        updates.append({
                            'flow_id': flow_id,
                            'plan_id': plan_id,
                            'task_id': task_id,
                            'task_name': task.get('name'),
                            'old_status': old_status,
                            'new_status': new_status
                        })

                        updated_count += 1

                        self._log_action('task_status_update', task_id, {
                            'old_status': old_status,
                            'new_status': new_status
                        })

        self._save_flows(data)
        return updated_count, updates

    def batch_complete_plans(self) -> Tuple[int, List[Dict[str, Any]]]:
        """모든 Task가 완료된 Plan을 일괄 완료 처리

        Returns:
            (완료 처리된 Plan 수, 완료 상세 리스트)
        """
        data = self._load_flows()
        completed_count = 0
        completions = []

        for flow_id, flow in data.get('flows', {}).items():
            for plan_id, plan in flow.get('plans', {}).items():
                if plan.get('completed', False):
                    continue

                tasks = plan.get('tasks', {})
                if not tasks:
                    continue

                # 모든 Task가 completed 상태인지 확인
                all_completed = all(
                    task.get('status') == 'completed'
                    for task in tasks.values()
                )

                if all_completed:
                    if not self.dry_run:
                        plan['completed'] = True
                        plan['completed_at'] = datetime.now().isoformat()

                        # Context 기록
                        record_plan_action(flow_id, plan_id, 'batch_completed', {
                            'plan_name': plan.get('name'),
                            'task_count': len(tasks)
                        })

                    completions.append({
                        'flow_id': flow_id,
                        'flow_name': flow.get('name'),
                        'plan_id': plan_id,
                        'plan_name': plan.get('name'),
                        'task_count': len(tasks)
                    })

                    completed_count += 1

                    self._log_action('plan_complete', plan_id, {
                        'plan_name': plan.get('name'),
                        'task_count': len(tasks)
                    })

        self._save_flows(data)
        return completed_count, completions

    def batch_delete_empty_plans(self) -> Tuple[int, List[Dict[str, Any]]]:
        """Task가 없는 빈 Plan 일괄 삭제

        Returns:
            (삭제된 Plan 수, 삭제 상세 리스트)
        """
        data = self._load_flows()
        deleted_count = 0
        deletions = []

        for flow_id, flow in data.get('flows', {}).items():
            plans_to_delete = []

            for plan_id, plan in flow.get('plans', {}).items():
                tasks = plan.get('tasks', {})
                if not tasks:
                    plans_to_delete.append(plan_id)

                    deletions.append({
                        'flow_id': flow_id,
                        'flow_name': flow.get('name'),
                        'plan_id': plan_id,
                        'plan_name': plan.get('name')
                    })

                    self._log_action('plan_delete', plan_id, {
                        'plan_name': plan.get('name'),
                        'reason': 'empty_plan'
                    })

            # 실제 삭제
            if not self.dry_run:
                for plan_id in plans_to_delete:
                    del flow['plans'][plan_id]
                    deleted_count += 1

                    # Context 기록
                    record_plan_action(flow_id, plan_id, 'batch_deleted', {
                        'reason': 'empty_plan'
                    })

        self._save_flows(data)
        return deleted_count, deletions

    def batch_add_tasks(self, 
                       plan_filter: Callable[[Dict[str, Any]], bool],
                       task_names: List[str]) -> Tuple[int, List[Dict[str, Any]]]:
        """특정 Plan들에 일괄 Task 추가

        Args:
            plan_filter: Plan 필터 함수
            task_names: 추가할 Task 이름 리스트

        Returns:
            (추가된 Task 수, 추가 상세 리스트)
        """
        data = self._load_flows()
        added_count = 0
        additions = []

        for flow_id, flow in data.get('flows', {}).items():
            for plan_id, plan in flow.get('plans', {}).items():
                if plan_filter(plan):
                    for task_name in task_names:
                        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}_{added_count:06x}"

                        new_task = {
                            'id': task_id,
                            'name': task_name,
                            'status': 'todo',
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }

                        if not self.dry_run:
                            if 'tasks' not in plan:
                                plan['tasks'] = {}
                            plan['tasks'][task_id] = new_task

                            # Context 기록
                            record_task_action(flow_id, task_id, 'batch_created', {
                                'task_name': task_name,
                                'plan_name': plan.get('name')
                            })

                        additions.append({
                            'flow_id': flow_id,
                            'plan_id': plan_id,
                            'task_id': task_id,
                            'task_name': task_name,
                            'plan_name': plan.get('name')
                        })

                        added_count += 1

                        self._log_action('task_add', task_id, {
                            'task_name': task_name,
                            'plan_id': plan_id
                        })

        self._save_flows(data)
        return added_count, additions

    def batch_update_flow_names(self, 
                               name_mapper: Callable[[str], str]) -> Tuple[int, List[Dict[str, Any]]]:
        """Flow 이름 일괄 변경

        Args:
            name_mapper: 이름 변환 함수 (기존 이름 -> 새 이름)

        Returns:
            (변경된 Flow 수, 변경 상세 리스트)
        """
        data = self._load_flows()
        updated_count = 0
        updates = []

        for flow_id, flow in data.get('flows', {}).items():
            old_name = flow.get('name', '')
            new_name = name_mapper(old_name)

            if old_name != new_name:
                if not self.dry_run:
                    flow['name'] = new_name
                    flow['updated_at'] = datetime.now().isoformat()

                    # Context 기록
                    record_flow_action(flow_id, 'batch_renamed', {
                        'old_name': old_name,
                        'new_name': new_name
                    })

                updates.append({
                    'flow_id': flow_id,
                    'old_name': old_name,
                    'new_name': new_name
                })

                updated_count += 1

                self._log_action('flow_rename', flow_id, {
                    'old_name': old_name,
                    'new_name': new_name
                })

        self._save_flows(data)
        return updated_count, updates

    def get_batch_log(self) -> List[Dict[str, Any]]:
        """일괄 작업 로그 반환"""
        return self.batch_log

    def clear_batch_log(self):
        """일괄 작업 로그 초기화"""
        self.batch_log = []

# 편의 함수들
def batch_complete_all_todo_tasks() -> Tuple[int, List[Dict[str, Any]]]:
    """모든 todo 상태 Task를 completed로 변경"""
    processor = FlowBatchProcessor()
    return processor.batch_update_task_status(
        lambda task: task.get('status') == 'todo',
        'completed'
    )

def batch_skip_error_tasks() -> Tuple[int, List[Dict[str, Any]]]:
    """모든 error 상태 Task를 skip으로 변경"""
    processor = FlowBatchProcessor()
    return processor.batch_update_task_status(
        lambda task: task.get('status') == 'error',
        'skip'
    )

def batch_cleanup_empty_plans() -> Tuple[int, List[Dict[str, Any]]]:
    """빈 Plan 정리"""
    processor = FlowBatchProcessor()
    return processor.batch_delete_empty_plans()

def batch_add_default_tasks(plan_name_pattern: str, default_tasks: List[str]) -> Tuple[int, List[Dict[str, Any]]]:
    """특정 패턴의 Plan에 기본 Task 추가"""
    processor = FlowBatchProcessor()
    return processor.batch_add_tasks(
        lambda plan: plan_name_pattern.lower() in plan.get('name', '').lower(),
        default_tasks
    )
