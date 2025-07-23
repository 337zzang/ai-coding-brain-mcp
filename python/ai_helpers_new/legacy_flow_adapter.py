# legacy_flow_adapter.py
'''
레거시 Flow 인터페이스 어댑터
기존 코드와의 호환성 유지
'''

from typing import Dict, Any, Optional
from .util import ok, err
import os
import warnings

from .flow_manager import FlowManager
from .exceptions import ValidationError


class LegacyFlowAdapter:
    """
    레거시 인터페이스를 새로운 FlowManager로 변환
    기존 FlowManagerUnified와 동일한 인터페이스 제공
    """

    def __init__(self, flow_manager: Optional[FlowManager] = None):
        self._manager = flow_manager or FlowManager()
        self._flows_cache = None
        self._cache_dirty = True
        self._previous_flow_id: Optional[str] = None  # o3 권장사항 추가

        # 레거시 경고
        warnings.warn(
            "LegacyFlowAdapter는 하위 호환성을 위한 것입니다. "
            "새 코드에서는 FlowManager를 직접 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )

    # === 레거시 속성 ===

    @property
    def flows(self) -> Dict[str, Dict[str, Any]]:
        """레거시 flows 속성 (딕셔너리 형태)"""
        if self._cache_dirty:
            self._sync_flows()
        return self._flows_cache

    @flows.setter
    def flows(self, value: Dict[str, Dict[str, Any]]):
        """레거시 flows setter"""
        if not isinstance(value, dict):
            raise ValidationError("flows는 딕셔너리여야 합니다")

        # 기존 flows와 비교하여 변경사항 적용
        current_flows = {f.id: f for f in self._manager.list_flows()}

        # 삭제된 flows 처리
        for flow_id in list(current_flows.keys()):
            if flow_id not in value:
                self._manager.delete_flow(flow_id)

        # 추가/수정된 flows 처리
        for flow_id, flow_data in value.items():
            if isinstance(flow_data, dict):
                # Flow 객체로 변환하여 저장
                from .domain.models import Flow
                flow = Flow.from_dict(flow_data)
                self._manager._service.save_flow(flow)

        self._cache_dirty = True

    @property
    def current_flow(self) -> Optional[Dict[str, Any]]:
        """레거시 current_flow 속성"""
        flow = self._manager.current_flow
        return flow.to_dict() if flow else None

    @current_flow.setter
    def current_flow(self, value: Dict[str, Any]):
        """레거시 current_flow setter"""
        if isinstance(value, dict) and 'id' in value:
            self._manager.current_flow = value['id']
        elif isinstance(value, str):
            self._manager.current_flow = value
        else:
            raise ValidationError("current_flow는 딕셔너리 또는 문자열이어야 합니다")

    @property
    def current_project(self) -> Optional[str]:
        """현재 프로젝트"""
        return self._manager.current_project

    @current_project.setter
    def current_project(self, value: str):
        """현재 프로젝트 설정"""
        self._manager.current_project = value

    # === 레거시 메서드 ===

    def create_flow(self, name: str) -> Dict[str, Any]:
        """Flow 생성 (레거시)"""
        flow = self._manager.create_flow(name, self.current_project)
        self._cache_dirty = True
        return flow.to_dict()

    def get_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Flow 조회 (레거시)"""
        flow = self._manager.get_flow(flow_id)
        return flow.to_dict() if flow else None

    def list_flows(self) -> list:
        """Flow 목록 (레거시)"""
        flows = self._manager.list_flows(self.current_project)
        return [f.to_dict() for f in flows]

    def delete_flow(self, flow_id: str):
        """Flow 삭제 (레거시)"""
        self._manager.delete_flow(flow_id)
        self._cache_dirty = True

    def add_plan(self, flow_id: str, name: str) -> Dict[str, Any]:
        """Plan 추가 (레거시)"""
        plan = self._manager.create_plan(flow_id, name)
        self._cache_dirty = True
        return plan.to_dict()

    def add_task(self, flow_id: str, plan_id: str, name: str) -> Dict[str, Any]:
        """Task 추가 (레거시)"""
        task = self._manager.create_task(flow_id, plan_id, name)
        self._cache_dirty = True
        return task.to_dict()

    def update_task_status(self, flow_id: str, plan_id: str, task_id: str, status: str):
        """Task 상태 업데이트 (레거시)"""
        self._manager.update_task_status(flow_id, plan_id, task_id, status)
        self._cache_dirty = True

    def update_task_context(self, flow_id: str, plan_id: str, task_id: str, context: Dict[str, Any]):
        """Task context 업데이트 (레거시)"""
        self._manager.update_task_context(flow_id, plan_id, task_id, context)
        self._cache_dirty = True

    def add_task_action(self, flow_id: str, plan_id: str, task_id: str, action: str, details: Dict[str, Any]):
        """Task 액션 추가 (레거시)"""
        # 새 시스템에서는 Context로 자동 기록됨
        # 호환성을 위해 context에 추가
        context = {'actions': [{'type': action, 'details': details}]}
        self._manager.update_task_context(flow_id, plan_id, task_id, context)
        self._cache_dirty = True

    # === 헬퍼 메서드 ===

    def _sync_flows(self):
        """flows 캐시 동기화"""
        flows = self._manager.list_flows()
        self._flows_cache = {f.id: f.to_dict() for f in flows}
        self._cache_dirty = False

    def save(self):
        """저장 (레거시 - 실제로는 자동 저장됨)"""
        # 새 시스템에서는 모든 변경사항이 즉시 저장됨
        pass

    def load(self):
        """로드 (레거시 - 실제로는 자동 로드됨)"""
        self._cache_dirty = True

    # === 통계 (레거시) ===

    def get_stats(self) -> Dict[str, Any]:
        """통계 (레거시)"""
        stats = self._manager.get_statistics()

    def switch_project(self, name: str) -> Dict[str, Any]:
        """프로젝트(Flow) 전환"""
        # 현재 Flow 저장
        current = self._manager.current_flow
        if current:
            self._previous_flow_id = current.id

        # Flow 찾기 또는 생성
        flows = self._manager.list_flows()
        target_flow = None
        for flow in flows:
            if flow.name == name:
                target_flow = flow
                break

        if not target_flow:
            # Flow가 없으면 에러 반환
            return err(f"Flow '{name}'을 찾을 수 없습니다. '/flow create {name}'으로 먼저 생성하세요.")

        # current_flow 설정
        self._manager._current_flow_id = target_flow.id
        self._flows_cache = None  # 캐시 무효화
        self._cache_dirty = True

        return {'ok': True, 'data': {
            'id': target_flow.id,
            'name': target_flow.name,
            'switched': True
        }}


    def switch_to_previous(self) -> Dict[str, Any]:
        """이전 Flow로 전환"""
        if not self._previous_flow_id:
            return {'ok': False, 'error': '이전 Flow가 없습니다'}

        # 현재와 이전 교체
        current = self._manager._current_flow_id
        self._manager._current_flow_id = self._previous_flow_id
        self._previous_flow_id = current

        self._flows_cache = None
        self._cache_dirty = True

        flow = self._manager.current_flow
        return {'ok': True, 'data': {
            'id': flow.id,
            'name': flow.name,
            'switched': True
        }}


    def get_status(self) -> Dict[str, Any]:
        """현재 Flow 상태 정보"""
        flow = self._manager.current_flow
        if not flow:
            return {'ok': False, 'error': '활성 Flow가 없습니다'}

        # 통계 계산
        total_plans = len(flow.plans)
        total_tasks = sum(len(plan.tasks) for plan in flow.plans.values())
        completed_tasks = sum(
            1 for plan in flow.plans.values()
            for task in plan.tasks.values()
            if task.status in ('completed', 'reviewing')
        )

        progress = 0
        if total_tasks > 0:
            progress = int(completed_tasks / total_tasks * 100)

        return {'ok': True, 'data': {
            'project': {
                'name': flow.name,
                'path': os.getcwd()  # 현재 작업 디렉토리 사용
            },
            'flow': {
                'id': flow.id,
                'plans': total_plans,
                'tasks': total_tasks,
                'completed': completed_tasks,
                'progress': progress,
                'last_activity': flow.updated_at or flow.created_at
            }
        }}


    def create_project(self, name: str, template: str = 'default') -> Dict[str, Any]:
        """새 프로젝트(Flow) 생성"""
        try:
            flow = self._manager.create_flow(name=name)
            return {'ok': True, 'data': {
                'id': flow.id,
                'name': flow.name,
                'created': True,
                'template': template
            }}
        except Exception as e:
            return {'ok': False, 'error': str(e)}


    def archive_flow(self, name: str) -> Dict[str, Any]:
        """Flow 아카이브 (soft delete)"""
        flows = self._manager.list_flows()
        target_flow = None

        for flow in flows:
            if flow.name == name:
                target_flow = flow
                break

        if not target_flow:
            return {'ok': False, 'error': f"Flow '{name}'를 찾을 수 없습니다"}

        # archived 플래그 설정
        target_flow.archived = True

        # 저장
        if hasattr(self._manager, '_service') and self._manager._service:
            self._manager._service.save_flow(target_flow)

        return {'ok': True, 'data': f"Flow '{name}' 아카이브됨"}


    def restore_flow(self, name: str) -> Dict[str, Any]:
        """아카이브된 Flow 복원"""
        flows = self._manager.list_flows()
        target_flow = None

        for flow in flows:
            if flow.name == name and getattr(flow, 'archived', False):
                target_flow = flow
                break

        if not target_flow:
            return {'ok': False, 'error': f"아카이브된 Flow '{name}'를 찾을 수 없습니다"}

        # archived 플래그 해제
        target_flow.archived = False

        # 저장
        if hasattr(self._manager, '_service') and self._manager._service:
            self._manager._service.save_flow(target_flow)

        return {'ok': True, 'data': f"Flow '{name}' 복원됨"}


# 기존 FlowManagerUnified를 대체하는 팩토리 함수
def create_flow_manager(legacy: bool = False, **kwargs) -> Any:
    """
    Flow Manager 생성

    Args:
        legacy: True면 레거시 어댑터 반환
        **kwargs: FlowManager 생성 인자

    Returns:
        FlowManager 또는 LegacyFlowAdapter
    """
    manager = FlowManager(**kwargs)

    if legacy:
        return LegacyFlowAdapter(manager)

    return manager

    # ========== o3 권장사항에 따른 추가 메서드 ==========
    # FlowCommandRouter가 필요로 하는 상위 레벨 API


# 컨텍스트 관련 레거시 호환 함수

def update_task_context_legacy(flow_id: str, plan_id: str, task_id: str, key: str, value: Any) -> Dict[str, Any]:
    """레거시 호환용 - key/value 방식을 새 API로 변환"""
    from .flow_manager import FlowManager
    fm = FlowManager(context_enabled=True)
    return fm.update_task_context(flow_id, plan_id, task_id, {key: value}, merge=True)

def save_task_context(task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """간단한 컨텍스트 저장 - 현재 플로우 자동 감지"""
    from .flow_manager import FlowManager
    fm = FlowManager(context_enabled=True)

    # 현재 플로우에서 task 찾기
    flows = fm.list_flows()
    for flow in flows:
        for plan_id, plan in flow.plans.items():
            if task_id in plan.tasks:
                return fm.update_task_context(flow.id, plan_id, task_id, context, merge=True)

    # 찾지 못하면 파일로 저장 (fallback)
    import json
    from datetime import datetime
    fallback_file = f"task_contexts/{task_id}_context.json"
    os.makedirs("task_contexts", exist_ok=True)

    with open(fallback_file, 'w') as f:
        json.dump({
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'context': context
        }, f, indent=2)

    return context
