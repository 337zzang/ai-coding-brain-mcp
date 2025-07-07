from events.event_bus import get_event_bus
from events.event_types import EventTypes, WorkflowEvent, TaskEvent, create_task_started_event, create_task_completed_event
"""
개선된 워크플로우 매니저
- 단일 플랜 관리
- 원자적 저장
- 프로젝트별 경로 지원
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from .models import Plan, Task, TaskStatus
from python.utils.io_helpers import write_json, read_json


class WorkflowManager:
    """개선된 워크플로우 관리자 - 단일 플랜 중심"""

    def __init__(self, data_file: str = "memory/workflow.json"):
        """
        Args:
            data_file: 워크플로우 데이터 파일 경로
        """
        self.data_file = data_file
        self.project_name = os.path.basename(os.getcwd())
        self.current_plan: Optional[Plan] = None
        self.plans: List[Plan] = []  # 호환성을 위해 유지
        self.history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "project_name": self.project_name,
            "version": "2.0",
            "last_updated": datetime.now().isoformat()
        }
        self.load_data()

    def load_data(self) -> None:
        """워크플로우 데이터 로드"""
        if not os.path.exists(self.data_file):
            print(f"📄 새로운 워크플로우 파일 생성: {self.data_file}")
            return

        try:
            # 버전 2.0 형식 확인
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get("metadata", {}).get("version") == "2.0":
                self._load_v2_format(data)
            else:
                self._migrate_from_legacy(data)

        except Exception as e:
            print(f"❌ 워크플로우 로드 실패: {e}")
            self.current_plan = None
            self.plans = []
            self.history = []

    def _load_v2_format(self, data: Dict[str, Any]) -> None:
        """버전 2.0 형식 로드"""
        # 현재 플랜
        if data.get("current_plan"):
            self.current_plan = Plan.from_dict(data["current_plan"])
            self.plans = [self.current_plan]  # 호환성
        else:
            self.plans = []

        # 히스토리
        self.history = data.get("history", [])

        # 메타데이터
        self.metadata = data.get("metadata", self.metadata)

        print(f"✅ 워크플로우 로드 완료: {self.current_plan.name if self.current_plan else '플랜 없음'}")

    def _migrate_from_legacy(self, data: Dict[str, Any]) -> None:
        """레거시 형식에서 마이그레이션"""
        print("🔄 레거시 워크플로우 형식 감지. 마이그레이션 시작...")

        plans_data = data.get("plans", [])
        current_plan_id = data.get("current_plan_id")

        # Plan 객체 생성
        for plan_data in plans_data:
            if isinstance(plan_data, dict):
                plan = Plan.from_dict(plan_data)
                if plan.id == current_plan_id:
                    self.current_plan = plan
                    self.plans = [plan]
                    print(f"  ✓ 현재 플랜 설정: {plan.name}")
                else:
                    # 다른 플랜은 히스토리로
                    self.history.append({
                        "plan": plan_data,
                        "archived_at": datetime.now().isoformat(),
                        "reason": "migration"
                    })

        # 현재 플랜이 없으면 첫 번째 플랜 사용
        if not self.current_plan and plans_data:
            self.current_plan = Plan.from_dict(plans_data[0])
            self.plans = [self.current_plan]
            print(f"  ✓ 첫 번째 플랜을 현재 플랜으로 설정: {self.current_plan.name}")

        # 기존 history 병합
        if 'history' in data:
            self.history.extend(data['history'])

        # 즉시 새 형식으로 저장
        self.save_data()
        print("✅ 마이그레이션 완료!")

    def save_data(self) -> None:
        """워크플로우 데이터 저장 (원자적 쓰기)"""
        self.metadata["last_updated"] = datetime.now().isoformat()

        data = {
            "current_plan": self.current_plan.to_dict() if self.current_plan else None,
            "history": self.history[-10:],  # 최근 10개만 유지
            "metadata": self.metadata
        }

        try:
            write_json(data, Path(self.data_file))
            print(f"💾 워크플로우 저장 완료 (원자적 쓰기)")
        except Exception as e:
            print(f"❌ 워크플로우 저장 실패: {e}")
            # fallback to direct write
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def create_plan(self, name: str, description: str = "") -> Plan:
        """새 플랜 생성"""
        # 현재 플랜이 있으면 히스토리로 이동
        if self.current_plan:
            self.history.append({
                "plan": self.current_plan.to_dict(),
                "archived_at": datetime.now().isoformat(),
                "reason": "new_plan_created"
            })
            print(f"📦 이전 플랜 '{self.current_plan.name}'이(가) 히스토리로 이동되었습니다.")

        # 새 플랜 생성
        self.current_plan = Plan(name=name, description=description)
        self.plans = [self.current_plan]
        self.save_data()

        print(f"✨ 새 플랜 생성: {name}")
        return self.current_plan

    def get_current_plan(self) -> Optional[Plan]:
        """현재 활성 플랜 반환"""
        return self.current_plan

    def _find_plan(self, plan_id: str) -> Optional[Plan]:
        """ID로 플랜 찾기 (호환성)"""
        if self.current_plan and self.current_plan.id == plan_id:
            return self.current_plan
        return None

    def add_task(self, title: str, description: str = "") -> Optional[Task]:
        """현재 플랜에 작업 추가"""
        if not self.current_plan:
            print("❌ 활성 플랜이 없습니다.")
            return None

        task = self.current_plan.add_task(title, description)
        self.save_data()
        return task

    def complete_task(self, task_id: str, notes: str = "") -> bool:
        """작업 완료 처리"""
        if not self.current_plan:
            return False

        success = self.current_plan.complete_task(task_id, notes)
        if success:
            self.save_data()

            # 모든 작업이 완료되면 플랜도 완료 처리
            if self.current_plan.get_progress() == 100:
                print(f"🎉 플랜 '{self.current_plan.name}' 완료!")

        return success

    def get_next_task(self) -> Optional[Task]:
        """다음 작업 반환"""
        if not self.current_plan:
            return None
        return self.current_plan.get_next_task()

    def get_current_task(self) -> Optional[Task]:
        """현재 진행 중인 작업 반환"""
        if not self.current_plan:
            return None
        return self.current_plan.get_current_task()

    def start_task(self, task_id: str) -> bool:
        """작업 시작"""
        if not self.current_plan:
            return False

        for task in self.current_plan.tasks:
            if task.id == task_id:
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = datetime.now().isoformat()
                self.save_data()
                return True
        return False

    def get_history(self) -> List[Dict[str, Any]]:
        """작업 히스토리 반환"""
        history = []

        # 현재 플랜의 완료된 작업들
        if self.current_plan:
            for task in self.current_plan.tasks:
                if task.completed:
                    history.append({
                        'title': task.title,
                        'completed_at': task.completed_at,
                        'notes': task.result.get('notes', '')
                    })

        # 히스토리의 플랜들
        for hist in self.history:
            plan_data = hist.get('plan', {})
            history.append({
                'title': f"[플랜] {plan_data.get('name', 'Unknown')}",
                'completed_at': hist.get('archived_at', ''),
                'notes': hist.get('reason', '')
            })

        return history
