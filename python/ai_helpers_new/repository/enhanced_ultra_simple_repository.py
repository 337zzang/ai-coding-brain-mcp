"""
Enhanced Ultra Simple Repository - 폴더 기반 Plan 저장
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import tempfile
from datetime import datetime

from ..domain.models import Plan, Task, TaskStatus


class EnhancedUltraSimpleRepository:
    """폴더 기반 Plan 저장소

    구조:
    .ai-brain/flow/
    ├── plans/
    │   └── plan_20250725_001/
    │       ├── plan.json                    # Plan 메타데이터
    │       ├── 1.task_auth_refactor.jsonl   # Task 로그 (TaskLogger 사용)
    │       └── 2.task_user_service.jsonl    # Task 로그
    └── index.json                           # Plan 인덱스 (선택적)
    """

    def __init__(self, base_path: str = ".ai-brain/flow"):
        # Windows/Linux 호환을 위해 절대경로로 변환
        self.base = Path(base_path).resolve()
        self.plans_dir = self.base / "plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

        # 인덱스 파일 (빠른 검색용)
        self.index_file = self.base / "index.json"

        # 기존 단일 파일에서 마이그레이션
        self._migrate_legacy_plans()

    def save_plan(self, plan: Plan) -> None:
        """Plan 저장 - 폴더 구조로"""
        # Plan 폴더 생성
        plan_dir = self.plans_dir / plan.id
        plan_dir.mkdir(exist_ok=True)

        # plan.json 저장 (메타데이터만)
        plan_meta = {
            "id": plan.id,
            "name": plan.name,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "metadata": plan.metadata,
        }

        plan_file = plan_dir / "plan.json"
        self._atomic_write(plan_file, plan_meta)

        # tasks.json 저장 (Task 정보)
        tasks_data = {
            task_id: task.to_dict() 
            for task_id, task in plan.tasks.items()
        }
        tasks_file = plan_dir / "tasks.json"
        self._atomic_write(tasks_file, tasks_data)

        # 인덱스 업데이트
        self._update_index(plan)

    def load_plan(self, plan_id: str) -> Optional[Plan]:
        """Plan 로드 - 폴더 구조에서"""
        plan_dir = self.plans_dir / plan_id

        # 레거시 파일 확인 (호환성)
        legacy_file = self.base / f"{plan_id}.json"
        if legacy_file.exists() and not plan_dir.exists():
            # 레거시 파일 로드
            data = self._safe_read(legacy_file)
            if data:
                return Plan.from_dict(plan_data)(data)

        # 새 구조에서 로드
        plan_file = plan_dir / "plan.json"
        tasks_file = plan_dir / "tasks.json"

        if not plan_file.exists():
            return None

        # Plan 메타데이터 로드
        plan_meta = self._safe_read(plan_file)
        if not plan_meta:
            return None

        # Tasks 로드
        tasks_data = self._safe_read(tasks_file) or {}

        # Plan 재구성
        plan_data = plan_meta.copy()
        plan_data["tasks"] = tasks_data

        return Plan.from_dict(plan_data)

    def list_plan_ids(self) -> List[str]:
        """모든 Plan ID 목록"""
        plan_ids = []

        # 새 폴더 구조에서
        if self.plans_dir.exists():
            for plan_dir in self.plans_dir.iterdir():
                if plan_dir.is_dir() and (plan_dir / "plan.json").exists():
                    plan_ids.append(plan_dir.name)

        # 레거시 파일도 포함 (호환성)
        for plan_file in self.base.glob("plan_*.json"):
            plan_id = plan_file.stem
            if plan_id not in plan_ids:
                plan_ids.append(plan_id)

        return sorted(plan_ids)

    def delete_plan(self, plan_id: str) -> None:
        """Plan 삭제"""
        import shutil

        # 폴더 삭제
        plan_dir = self.plans_dir / plan_id
        if plan_dir.exists():
            shutil.rmtree(plan_dir)

        # 레거시 파일도 삭제
        legacy_file = self.base / f"{plan_id}.json"
        if legacy_file.exists():
            legacy_file.unlink()

        # 인덱스 업데이트
        self._remove_from_index(plan_id)

    def get_stats(self) -> Dict[str, Any]:
        """저장소 통계"""
        plan_count = len(self.list_plan_ids())

        # 폴더 크기 계산
        total_size = 0
        for plan_dir in self.plans_dir.iterdir():
            if plan_dir.is_dir():
                for file in plan_dir.rglob("*"):
                    if file.is_file():
                        total_size += file.stat().st_size

        return {
            "repository_type": "enhanced_folder_based",
            "plan_count": plan_count,
            "total_size_bytes": total_size,
            "storage_path": str(self.base)
        }

    # --- Private methods ---

    def _atomic_write(self, path: Path, data: Any) -> None:
        """원자적 파일 쓰기"""
        temp_file = path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(path)
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise

    def _safe_read(self, path: Path) -> Optional[Dict]:
        """안전한 파일 읽기"""
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return None

    def _migrate_legacy_plans(self) -> None:
        """레거시 단일 파일을 폴더 구조로 마이그레이션"""
        migrated = 0

        for plan_file in self.base.glob("plan_*.json"):
            plan_id = plan_file.stem
            plan_dir = self.plans_dir / plan_id

            # 이미 마이그레이션됨
            if plan_dir.exists():
                continue

            # 레거시 파일 로드
            data = self._safe_read(plan_file)
            if data:
                # Plan 객체로 변환 후 새 구조로 저장
                plan = Plan.from_dict(data)
                self.save_plan(plan)

                # 레거시 파일은 보존 (안전을 위해)
                # plan_file.unlink()

                migrated += 1

        if migrated > 0:
            print(f"✅ {migrated}개의 Plan을 폴더 구조로 마이그레이션했습니다.")

    def _update_index(self, plan: Plan) -> None:
        """인덱스 업데이트"""
        index = self._safe_read(self.index_file) or {}

        index[plan.id] = {
            "name": plan.name,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "task_count": len(plan.tasks)
        }

        self._atomic_write(self.index_file, index)

    def _remove_from_index(self, plan_id: str) -> None:
        """인덱스에서 제거"""
        index = self._safe_read(self.index_file) or {}
        if plan_id in index:
            del index[plan_id]
            self._atomic_write(self.index_file, index)


# 기존 Repository를 대체하는 팩토리 함수
def create_repository(base_path: str = ".ai-brain/flow") -> EnhancedUltraSimpleRepository:
    """Repository 생성 (향상된 버전)"""
    return EnhancedUltraSimpleRepository(base_path)
