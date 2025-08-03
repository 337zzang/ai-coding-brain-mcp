"""
극단적으로 단순화된 Flow Repository
- flow.json 없음
- plans 폴더 없음
- flow 폴더 바로 아래 plan 파일들
"""
import json
from collections import OrderedDict
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import shutil
from datetime import datetime

from ..domain.models import Plan, Task


class UltraSimpleRepository:
    """극단적으로 단순한 Repository"""

    def __init__(self, base_path: str = ".ai-brain/flow"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def _atomic_write(self, path: Path, data: dict) -> None:
        """원자적 쓰기"""
        tmp_path = path.with_suffix('.tmp')
        try:
            with tmp_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp_path.replace(path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def _safe_read(self, path: Path) -> Optional[dict]:
        """안전한 JSON 읽기"""
        if not path.exists():
            return None
        try:
            with path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    # --- Plan 관리 (flow 폴더에 직접 저장) ---

    def save_plan(self, plan: Plan) -> None:
        """Plan 저장 - flow 폴더에 직접"""
        plan_path = self.base / f"{plan.id}.json"
        self._atomic_write(plan_path, plan.to_dict())

    def load_plan(self, plan_id: str) -> Optional[Plan]:
        """Plan 로드"""
        plan_path = self.base / f"{plan_id}.json"
        data = self._safe_read(plan_path)
        if data:
            return Plan.from_dict(data)
        return None

    def list_plan_ids(self) -> List[str]:
        """모든 Plan ID 목록"""
        plan_ids = []
        for plan_file in self.base.glob("plan_*.json"):
            plan_ids.append(plan_file.stem)
        return sorted(plan_ids)

    def delete_plan(self, plan_id: str) -> None:
        """Plan 삭제"""
        plan_path = self.base / f"{plan_id}.json"
        if plan_path.exists():
            plan_path.unlink()

    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        plan_files = list(self.base.glob("plan_*.json"))

        # 가장 최근 수정 시간
        if plan_files:
            latest_modified = max(f.stat().st_mtime for f in plan_files)
            latest_modified_str = datetime.fromtimestamp(latest_modified).isoformat()
        else:
            latest_modified_str = None

        return {
            'plan_count': len(plan_files),
            'last_updated': latest_modified_str,
            'total_size': sum(f.stat().st_size for f in plan_files)
        }
