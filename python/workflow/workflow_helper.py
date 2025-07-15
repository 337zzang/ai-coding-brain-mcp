"""
독립적인 워크플로우 헬퍼
"""

import json
import os
from datetime import datetime
import time
from pathlib import Path

class WorkflowHelper:
    """워크플로우 전용 헬퍼"""

    def __init__(self):
        self.memory_path = Path("memory")
        self.workflow_path = self.memory_path / "workflow.json"
        self._workflow_integration = None

    @property
    def workflow_integration(self):
        if self._workflow_integration is None:
            try:
                from python.ai_helpers.workflow.workflow_integration import workflow_integration
                self._workflow_integration = workflow_integration
            except:
                pass
        return self._workflow_integration

    def get_current_workflow(self):
        """현재 워크플로우 상태"""
        try:
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('current_plan_id'):
                for plan in data.get('plans', []):
                    if plan['id'] == data['current_plan_id']:
                        tasks = plan.get('tasks', [])
                        completed = sum(1 for t in tasks if t.get('status') == 'completed')
                        progress = (completed / len(tasks) * 100) if tasks else 0
                        return {
                            'plan': plan,
                            'progress': progress
                        }
            return {'plan': None, 'progress': 0}
        except:
            return {'plan': None, 'progress': 0}

    def get_current_task(self):
        """현재 진행 중인 태스크"""
        workflow = self.get_current_workflow()
        if workflow['plan']:
            for task in workflow['plan'].get('tasks', []):
                if task.get('status') == 'in_progress':
                    return task
        return None

    def update_task_status(self, status, note=None):
        """태스크 상태 업데이트"""
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
                return True
            else:
                print(f"❌ 태스크 업데이트 실패")
                return False
        else:
            print("⚠️ 현재 진행 중인 태스크가 없습니다.")
            return False

    def show_status(self):
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

    def task_context(self, task_name=None):
        """태스크 실행 컨텍스트"""
        class TaskContext:
            def __init__(self, name):
                self.name = name
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                if self.name:
                    print(f"\n🔧 시작: {self.name}")
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                if exc_type is None:
                    if self.name:
                        print(f"✅ 완료: {self.name} ({duration:.2f}초)")
                else:
                    if self.name:
                        print(f"❌ 실패: {self.name} - {exc_val}")
                return False

        return TaskContext(task_name)

# 전역 인스턴스 생성
workflow = WorkflowHelper()
