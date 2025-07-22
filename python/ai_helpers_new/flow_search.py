"""Flow 검색 및 필터링 기능"""
import re
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from .domain.models import TaskStatus

class FlowSearchEngine:
    """Flow, Plan, Task 검색 엔진"""

    def __init__(self):
        self.search_cache = {}

    def search_flows(self, flows: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Flow 검색

        Args:
            flows: 전체 Flow 데이터
            query: 검색어

        Returns:
            매칭된 Flow 리스트
        """
        results = []
        query_lower = query.lower()

        for flow_id, flow in flows.items():
            # Flow 이름 검색
            if query_lower in flow.get('name', '').lower():
                results.append({
                    'flow_id': flow_id,
                    'flow': flow,
                    'match_type': 'name',
                    'score': 1.0
                })
                continue

            # Plan 이름에서 검색
            for plan_id, plan in flow.get('plans', {}).items():
                if query_lower in plan.get('name', '').lower():
                    results.append({
                        'flow_id': flow_id,
                        'flow': flow,
                        'match_type': 'plan_name',
                        'match_plan_id': plan_id,
                        'score': 0.8
                    })
                    break

            # Task 이름에서 검색
            for plan_id, plan in flow.get('plans', {}).items():
                for task_id, task in plan.get('tasks', {}).items():
                    if query_lower in task.get('name', '').lower():
                        results.append({
                            'flow_id': flow_id,
                            'flow': flow,
                            'match_type': 'task_name',
                            'match_plan_id': plan_id,
                            'match_task_id': task_id,
                            'score': 0.6
                        })
                        break

        # 점수 순으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def filter_flows(self, flows: Dict[str, Any], **filters) -> List[Dict[str, Any]]:
        """Flow 필터링

        Args:
            flows: 전체 Flow 데이터
            **filters: 필터 조건들
                - created_after: datetime
                - created_before: datetime
                - has_plans: bool
                - plan_count_min: int
                - plan_count_max: int
                - name_pattern: str (regex)

        Returns:
            필터링된 Flow 리스트
        """
        results = []

        for flow_id, flow in flows.items():
            # 생성일 필터
            if 'created_after' in filters or 'created_before' in filters:
                created_at = flow.get('created_at', '')
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

                        if 'created_after' in filters and created_dt < filters['created_after']:
                            continue
                        if 'created_before' in filters and created_dt > filters['created_before']:
                            continue
                    except:
                        continue

            # Plan 존재 여부
            plans = flow.get('plans', {})
            if 'has_plans' in filters:
                if filters['has_plans'] and not plans:
                    continue
                if not filters['has_plans'] and plans:
                    continue

            # Plan 개수 필터
            plan_count = len(plans)
            if 'plan_count_min' in filters and plan_count < filters['plan_count_min']:
                continue
            if 'plan_count_max' in filters and plan_count > filters['plan_count_max']:
                continue

            # 이름 패턴 필터
            if 'name_pattern' in filters:
                pattern = filters['name_pattern']
                if not re.search(pattern, flow.get('name', ''), re.IGNORECASE):
                    continue

            results.append({
                'flow_id': flow_id,
                'flow': flow,
                'plan_count': plan_count
            })

        return results

    def filter_plans(self, flow: Dict[str, Any], **filters) -> List[Dict[str, Any]]:
        """Plan 필터링

        Args:
            flow: Flow 데이터
            **filters: 필터 조건들
                - completed: bool
                - has_tasks: bool
                - task_count_min: int
                - name_contains: str

        Returns:
            필터링된 Plan 리스트
        """
        results = []

        for plan_id, plan in flow.get('plans', {}).items():
            # 완료 상태 필터
            if 'completed' in filters:
                if plan.get('completed', False) != filters['completed']:
                    continue

            # Task 존재 여부
            tasks = plan.get('tasks', {})
            if 'has_tasks' in filters:
                if filters['has_tasks'] and not tasks:
                    continue
                if not filters['has_tasks'] and tasks:
                    continue

            # Task 개수 필터
            task_count = len(tasks)
            if 'task_count_min' in filters and task_count < filters['task_count_min']:
                continue

            # 이름 포함 필터
            if 'name_contains' in filters:
                if filters['name_contains'].lower() not in plan.get('name', '').lower():
                    continue

            results.append({
                'plan_id': plan_id,
                'plan': plan,
                'task_count': task_count
            })

        return results

    def filter_tasks(self, plan: Dict[str, Any], **filters) -> List[Dict[str, Any]]:
        """Task 필터링

        Args:
            plan: Plan 데이터
            **filters: 필터 조건들
                - status: str or List[str]
                - name_contains: str
                - created_after: datetime

        Returns:
            필터링된 Task 리스트
        """
        results = []

        for task_id, task in plan.get('tasks', {}).items():
            # 상태 필터
            if 'status' in filters:
                status_filter = filters['status']
                if isinstance(status_filter, str):
                    status_filter = [status_filter]

                if task.get('status') not in status_filter:
                    continue

            # 이름 포함 필터
            if 'name_contains' in filters:
                if filters['name_contains'].lower() not in task.get('name', '').lower():
                    continue

            # 생성일 필터
            if 'created_after' in filters:
                created_at = task.get('created_at', '')
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if created_dt < filters['created_after']:
                            continue
                    except:
                        continue

            results.append({
                'task_id': task_id,
                'task': task
            })

        return results

    def advanced_search(self, flows: Dict[str, Any], 
                       search_func: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        """고급 검색 (사용자 정의 함수)

        Args:
            flows: 전체 Flow 데이터
            search_func: 검색 조건 함수 (Flow를 받아서 bool 반환)

        Returns:
            매칭된 Flow 리스트
        """
        results = []

        for flow_id, flow in flows.items():
            if search_func(flow):
                results.append({
                    'flow_id': flow_id,
                    'flow': flow
                })

        return results

# 편의 함수들
def search_flows_by_name(flows: Dict[str, Any], name: str) -> List[Dict[str, Any]]:
    """이름으로 Flow 검색"""
    engine = FlowSearchEngine()
    return engine.search_flows(flows, name)

def get_active_flows(flows: Dict[str, Any]) -> List[Dict[str, Any]]:
    """진행 중인 Flow 찾기 (완료되지 않은 Plan이 있는 Flow)"""
    engine = FlowSearchEngine()

    def is_active(flow):
        for plan in flow.get('plans', {}).values():
            if not plan.get('completed', False):
                return True
        return False

    return engine.advanced_search(flows, is_active)

def get_flows_with_pending_tasks(flows: Dict[str, Any]) -> List[Dict[str, Any]]:
    """미완료 Task가 있는 Flow 찾기"""
    engine = FlowSearchEngine()

    def has_pending_tasks(flow):
        for plan in flow.get('plans', {}).values():
            for task in plan.get('tasks', {}).values():
                if task.get('status') not in ['completed', 'skip']:
                    return True
        return False

    return engine.advanced_search(flows, has_pending_tasks)

def get_recent_flows(flows: Dict[str, Any], days: int = 7) -> List[Dict[str, Any]]:
    """최근 N일 내 생성된 Flow 찾기"""
    engine = FlowSearchEngine()
    cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

    return engine.filter_flows(flows, created_after=cutoff_date)
