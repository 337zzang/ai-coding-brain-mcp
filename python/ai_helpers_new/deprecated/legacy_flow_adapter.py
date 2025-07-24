# legacy_flow_adapter.py
'''
레거시 Flow 인터페이스 어댑터
기존 코드와의 호환성 유지
'''

from typing import Dict, Any, Optional
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

        # 레거시 형식으로 변환
        return {
            'flows': stats['total_flows'],
            'plans': stats['total_plans'],
            'tasks': stats['total_tasks'],
            'completed': stats['completed_tasks'],
            'percentage': int(stats['completion_rate'] * 100)
        }


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
