"""
워크플로우와 통합된 헬퍼 시스템 - 간단한 버전
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class WorkflowIntegratedHelpers:
    """기존 helpers를 워크플로우와 통합"""

    def __init__(self, base_helpers):
        self.base_helpers = base_helpers
        self.project_root = Path(__file__).parent.parent.parent
        self.memory_path = self.project_root / "memory"
        self.workflow_path = self.memory_path / "workflow.json"
        self._workflow_integration = None
        self._usage_shown = set()

        # 기존 helpers의 모든 메서드를 이 객체에 복사
        for attr_name in dir(base_helpers):
            if not attr_name.startswith('_'):
                attr = getattr(base_helpers, attr_name)
                if not hasattr(self, attr_name):  # 기존 메서드 우선
                    setattr(self, attr_name, attr)

    @property
    def workflow_integration(self):
        """지연 로드로 순환 참조 방지"""
        if self._workflow_integration is None:
            try:
                from .workflow.workflow_integration import workflow_integration
                self._workflow_integration = workflow_integration
            except:
                pass
        return self._workflow_integration

    # 워크플로우 관련 새 메서드들
    def get_current_workflow(self) -> Dict[str, Any]:
        """현재 워크플로우 상태 가져오기"""
        try:
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('current_plan_id'):
                for plan in data.get('plans', []):
                    if plan['id'] == data['current_plan_id']:
                        return {
                            'plan': plan,
                            'progress': self._calculate_progress(plan)
                        }
            return {'plan': None, 'progress': 0}
        except:
            return {'plan': None, 'progress': 0}

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """현재 진행 중인 태스크 가져오기"""
        workflow = self.get_current_workflow()
        if workflow['plan']:
            for task in workflow['plan'].get('tasks', []):
                if task.get('status') == 'in_progress':
                    return task
        return None

    def update_task_status(self, status: str, note: str = None):
        """현재 태스크 상태 업데이트"""
        task = self.get_current_task()
        if task and self.workflow_integration:
            updates = {'status': status}
            if note:
                updates['notes'] = [note]
            if status == 'completed':
                updates['completed_at'] = datetime.now().isoformat()

            result = self.workflow_integration.update_task(task['id'], updates)
            if result:
                print(f"✅ 태스크 상태 업데이트: {status}")
            else:
                print(f"❌ 태스크 업데이트 실패")
        else:
            print("⚠️ 현재 진행 중인 태스크가 없습니다.")

    def show_workflow_status(self):
        """워크플로우 상태 표시"""
        workflow = self.get_current_workflow()
        if workflow['plan']:
            plan = workflow['plan']
            print(f"\n📋 현재 워크플로우: {plan['name']}")
            print(f"진행률: {workflow['progress']:.1f}%")

            # 태스크 상태 요약
            tasks = plan.get('tasks', [])
            completed = sum(1 for t in tasks if t.get('status') == 'completed')
            in_progress = sum(1 for t in tasks if t.get('status') == 'in_progress')
            pending = len(tasks) - completed - in_progress

            print(f"태스크: 완료 {completed} | 진행 중 {in_progress} | 대기 {pending}")

            # 현재 태스크
            current = self.get_current_task()
            if current:
                print(f"\n현재 작업: {current['title']}")
        else:
            print("\n📋 활성 워크플로우 없음")

    def _calculate_progress(self, plan: Dict) -> float:
        """진행률 계산"""
        tasks = plan.get('tasks', [])
        if not tasks:
            return 0.0
        completed = sum(1 for t in tasks if t.get('status') == 'completed')
        return (completed / len(tasks)) * 100

    def with_workflow_task(self, task_name: str = None):
        """워크플로우 태스크 컨텍스트 매니저"""
        return WorkflowTaskContext(self, task_name)


class WorkflowTaskContext:
    """워크플로우 태스크 실행 컨텍스트"""

    def __init__(self, helpers_instance, task_name: str = None):
        self.helpers = helpers_instance
        self.task_name = task_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        if self.task_name:
            print(f"\n🔧 시작: {self.task_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type is None:
            if self.task_name:
                print(f"✅ 완료: {self.task_name} ({duration:.2f}초)")
        else:
            if self.task_name:
                print(f"❌ 실패: {self.task_name} - {exc_val}")

        return False
