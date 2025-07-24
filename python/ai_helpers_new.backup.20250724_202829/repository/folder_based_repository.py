"""
폴더 기반 Flow Repository 구현
- 원자적 쓰기 지원
- Flow/Plan 분리 저장
"""
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import shutil
from datetime import datetime
import uuid

from ..domain.models import Flow, Plan, Task


class FlowRepository(ABC):
    """Flow Repository 인터페이스"""

    @abstractmethod
    def save_flow(self, flow: Flow) -> None:
        pass

    @abstractmethod
    def load_flow(self, flow_id: str) -> Optional[Flow]:
        pass

    @abstractmethod
    def list_flows(self, project: Optional[str] = None) -> List[Flow]:
        pass

    @abstractmethod
    def delete_flow(self, flow_id: str) -> None:
        pass


class PlanRepository(ABC):
    """Plan Repository 인터페이스"""

    @abstractmethod
    def save_plan(self, plan: Plan) -> None:
        pass

    @abstractmethod
    def load_plan(self, flow_id: str, plan_id: str) -> Optional[Plan]:
        pass

    @abstractmethod
    def list_plans(self, flow_id: str) -> List[str]:
        pass

    @abstractmethod
    def delete_plan(self, flow_id: str, plan_id: str) -> None:
        pass


class JsonFileMixin:
    """JSON 파일 처리를 위한 믹스인"""

    @staticmethod
    def _atomic_write(path: Path, data: dict) -> None:
        """원자적 쓰기 - 임시 파일 생성 후 교체"""
        # 디렉토리가 없으면 생성
        path.parent.mkdir(parents=True, exist_ok=True)

        # 임시 파일에 쓰기
        tmp_path = path.with_suffix('.tmp')
        try:
            with tmp_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 원자적 교체
            tmp_path.replace(path)
        except Exception:
            # 실패 시 임시 파일 제거
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    @staticmethod
    def _safe_read(path: Path) -> Optional[dict]:
        """안전한 JSON 읽기"""
        if not path.exists():
            return None

        try:
            with path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # 손상된 파일 처리
            backup = path.with_suffix('.corrupt')
            shutil.copy2(path, backup)
            return None


class FileFlowRepository(JsonFileMixin, FlowRepository):
    """파일 기반 Flow Repository 구현"""

    def __init__(self, base_path: str = ".ai-brain/flow"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def _flow_dir(self, flow_id: str) -> Path:
        """Flow 디렉토리 경로"""
        return self.base / flow_id

    def _flow_meta_path(self, flow_id: str) -> Path:
        """Flow 메타데이터 파일 경로"""
        return self._flow_dir(flow_id) / "flow.json"

    def save_flow(self, flow: Flow) -> None:
        """Flow 저장"""
        flow_dir = self._flow_dir(flow.id)
        flow_dir.mkdir(exist_ok=True)

        # Flow 메타데이터만 저장 (plans 제외)
        flow_data = flow.to_dict()
        # plans 딕셔너리를 plan_ids 리스트로 변환
        if 'plans' in flow_data:
            flow_data['plan_ids'] = list(flow_data.get('plans', {}).keys())
            del flow_data['plans']

        self._atomic_write(self._flow_meta_path(flow.id), flow_data)

    def load_flow(self, flow_id: str) -> Optional[Flow]:
        """Flow 로드"""
        data = self._safe_read(self._flow_meta_path(flow_id))
        if not data:
            return None

        # plan_ids를 임시 plans 딕셔너리로 변환 (호환성)
        if 'plan_ids' in data and 'plans' not in data:
            data['plans'] = {}  # 빈 딕셔너리로 초기화

        return Flow.from_dict(data)

    def list_flows(self, project: Optional[str] = None) -> List[Flow]:
        """Flow 목록 조회"""
        flows = []

        if not self.base.exists():
            return flows

        for flow_dir in self.base.iterdir():
            if not flow_dir.is_dir():
                continue

            flow = self.load_flow(flow_dir.name)
            if flow and (project is None or flow.project == project):
                flows.append(flow)

        return flows

    def delete_flow(self, flow_id: str) -> None:
        """Flow 삭제"""
        flow_dir = self._flow_dir(flow_id)
        if flow_dir.exists():
            shutil.rmtree(flow_dir)


class FilePlanRepository(JsonFileMixin, PlanRepository):
    """파일 기반 Plan Repository 구현"""

    def __init__(self, base_path: str = ".ai-brain/flow"):
        self.base = Path(base_path)

    def _plans_dir(self, flow_id: str) -> Path:
        """Plans 디렉토리 경로"""
        return self.base / flow_id / "plans"

    def _plan_path(self, flow_id: str, plan_id: str) -> Path:
        """Plan 파일 경로"""
        return self._plans_dir(flow_id) / f"{plan_id}.json"

    def save_plan(self, plan: Plan) -> None:
        """Plan 저장"""
        # flow_id가 plan에 있어야 함
        if not hasattr(plan, 'flow_id'):
            raise ValueError("Plan must have flow_id attribute")

        plan_data = plan.to_dict()
        plan_data['flow_id'] = plan.flow_id  # flow_id 포함

        self._atomic_write(
            self._plan_path(plan.flow_id, plan.id), 
            plan_data
        )

    def load_plan(self, flow_id: str, plan_id: str) -> Optional[Plan]:
        """Plan 로드"""
        data = self._safe_read(self._plan_path(flow_id, plan_id))
        if not data:
            return None

        plan = Plan.from_dict(data)
        # flow_id 설정
        if hasattr(plan, '__dict__'):
            plan.__dict__['flow_id'] = flow_id

        return plan

    def list_plans(self, flow_id: str) -> List[str]:
        """Flow의 Plan ID 목록"""
        plans_dir = self._plans_dir(flow_id)
        if not plans_dir.exists():
            return []

        plan_ids = []
        for plan_file in plans_dir.glob("plan_*.json"):
            plan_ids.append(plan_file.stem)

        return sorted(plan_ids)

    def delete_plan(self, flow_id: str, plan_id: str) -> None:
        """Plan 삭제"""
        plan_path = self._plan_path(flow_id, plan_id)
        if plan_path.exists():
            plan_path.unlink()
