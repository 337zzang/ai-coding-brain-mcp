"""
단순화된 폴더 기반 Flow Repository
- Flow ID 제거
- 프로젝트당 하나의 Flow만 관리
"""
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import shutil
from datetime import datetime

from ..domain.models import Flow, Plan, Task


class JsonFileMixin:
    """JSON 파일 처리를 위한 믹스인"""

    @staticmethod
    def _atomic_write(path: Path, data: dict) -> None:
        """원자적 쓰기 - 임시 파일 생성 후 교체"""
        path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = path.with_suffix('.tmp')
        try:
            with tmp_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp_path.replace(path)
        except Exception:
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
            backup = path.with_suffix('.corrupt')
            shutil.copy2(path, backup)
            return None


class SimplifiedFlowRepository(JsonFileMixin):
    """단순화된 Flow Repository - ID 없음"""

    def __init__(self, base_path: str = ".ai-brain/flow"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)
        self.flow_path = self.base / "flow.json"

    def save_flow(self, flow_data: Dict[str, Any]) -> None:
        """Flow 저장 (ID 없음)"""
        # ID 필드 제거
        if 'id' in flow_data:
            del flow_data['id']

        # plans 제거 (plan_count만 유지)
        if 'plans' in flow_data:
            flow_data['plan_count'] = len(flow_data['plans'])
            del flow_data['plans']

        self._atomic_write(self.flow_path, flow_data)

    def load_flow(self) -> Optional[Dict[str, Any]]:
        """Flow 로드 (항상 하나만 존재)"""
        return self._safe_read(self.flow_path)

    def exists(self) -> bool:
        """Flow 존재 여부"""
        return self.flow_path.exists()

    def create_default_flow(self, project_name: str) -> Dict[str, Any]:
        """기본 Flow 생성"""
        flow_data = {
            'name': project_name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'plan_count': 0,
            'metadata': {}
        }
        self.save_flow(flow_data)
        return flow_data


class SimplifiedPlanRepository(JsonFileMixin):
    """단순화된 Plan Repository"""

    def __init__(self, base_path: str = ".ai-brain/flow"):
        self.base = Path(base_path)
        self.plans_dir = self.base / "plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    def save_plan(self, plan: Plan) -> None:
        """Plan 저장"""
        plan_path = self.plans_dir / f"{plan.id}.json"
        plan_data = plan.to_dict()

        # flow_id 제거 (필요없음)
        if 'flow_id' in plan_data:
            del plan_data['flow_id']

        self._atomic_write(plan_path, plan_data)

    def load_plan(self, plan_id: str) -> Optional[Plan]:
        """Plan 로드"""
        plan_path = self.plans_dir / f"{plan_id}.json"
        data = self._safe_read(plan_path)

        if data:
            return Plan.from_dict(data)
        return None

    def list_plan_ids(self) -> List[str]:
        """모든 Plan ID 목록"""
        if not self.plans_dir.exists():
            return []

        plan_ids = []
        for plan_file in self.plans_dir.glob("plan_*.json"):
            plan_ids.append(plan_file.stem)

        return sorted(plan_ids)

    def delete_plan(self, plan_id: str) -> None:
        """Plan 삭제"""
        plan_path = self.plans_dir / f"{plan_id}.json"
        if plan_path.exists():
            plan_path.unlink()

    def get_plan_count(self) -> int:
        """Plan 개수"""
        return len(self.list_plan_ids())
