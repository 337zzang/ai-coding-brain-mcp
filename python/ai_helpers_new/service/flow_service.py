"""
Flow 비즈니스 로직 서비스
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from ..domain.models import Flow, Plan, Task
from ..infrastructure.flow_repository import FlowRepository


class FlowService:
    """Flow 관련 비즈니스 로직"""

    def __init__(self, repository: FlowRepository):
        self.repository = repository
        self._current_flow_id: Optional[str] = None
        self._load_current_flow()

    def create_flow(self, name: str, metadata: Dict = None) -> Flow:
        """새 Flow 생성"""
        flow_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        flow = Flow(
            id=flow_id,
            name=name,
            metadata=metadata or {}
        )

        # 저장
        flows = self.repository.load_all()
        flows[flow_id] = flow
        self.repository.save_all(flows)

        return flow

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """특정 Flow 조회"""
        flows = self.repository.load_all()
        return flows.get(flow_id)

    def list_flows(self) -> List[Flow]:
        """모든 Flow 목록 조회"""
        flows = self.repository.load_all()
        return list(flows.values())

    def delete_flow(self, flow_id: str) -> bool:
        """Flow 삭제"""
        # 현재 Flow인 경우 current 해제
        if self._current_flow_id == flow_id:
            self._current_flow_id = None
            self._save_current_flow()

        return self.repository.delete(flow_id)

    def get_current_flow(self) -> Optional[Flow]:
        """현재 활성 Flow 조회"""
        if self._current_flow_id:
            return self.get_flow(self._current_flow_id)
        return None

    def set_current_flow(self, flow_id: str) -> bool:
        """현재 활성 Flow 설정"""
        if self.repository.exists(flow_id):
            self._current_flow_id = flow_id
            self._save_current_flow()
            return True
        return False

    def update_flow(self, flow: Flow) -> None:
        """Flow 업데이트"""
        flow.updated_at = datetime.now()
        self.repository.save(flow)

    def add_plan_to_flow(self, flow_id: str, plan: Plan) -> bool:
        """Flow에 Plan 추가"""
        flow = self.get_flow(flow_id)
        if flow:
            flow.plans[plan.id] = plan
            self.update_flow(flow)
            return True
        return False

    def remove_plan_from_flow(self, flow_id: str, plan_id: str) -> bool:
        """Flow에서 Plan 제거"""
        flow = self.get_flow(flow_id)
        if flow and plan_id in flow.plans:
            del flow.plans[plan_id]
            self.update_flow(flow)
            return True
        return False

    def _load_current_flow(self) -> None:
        """현재 Flow ID 로드 (파일에서)"""
        try:
            import os
            current_file = os.path.join(os.path.expanduser("~"), ".ai-flow", "current_flow.txt")
            if os.path.exists(current_file):
                with open(current_file, 'r') as f:
                    self._current_flow_id = f.read().strip()
        except Exception:
            self._current_flow_id = None

    def _save_current_flow(self) -> None:
        """현재 Flow ID 저장 (파일로)"""
        try:
            import os
            current_file = os.path.join(os.path.expanduser("~"), ".ai-flow", "current_flow.txt")
            os.makedirs(os.path.dirname(current_file), exist_ok=True)

            if self._current_flow_id:
                with open(current_file, 'w') as f:
                    f.write(self._current_flow_id)
            elif os.path.exists(current_file):
                os.remove(current_file)
        except Exception as e:
            print(f"Warning: Failed to save current flow: {e}")
