"""
WorkflowAwareHelpers - 워크플로우와 통합된 헬퍼 시스템
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from pathlib import Path

class WorkflowAwareHelpers:
    """워크플로우를 인식하는 헬퍼 클래스"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.memory_path = self.project_root / "memory"
        self.workflow_path = self.memory_path / "workflow.json"
        self._current_task = None
        self._usage_shown = set()

        # workflow_integration 동적 로드
        self._workflow_integration = None

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

    def __getattr__(self, name):
        """동적으로 기존 helpers 메서드 프록시"""
        # 먼저 기본 메서드 확인
        if name in ['get_current_workflow', 'get_current_task', 'update_task_status', 
                    'show_workflow_status', 'with_workflow_task']:
            return super().__getattribute__(name)

        # 기존 helpers에서 메서드 가져오기
        try:
            # 실제 helpers에서 메서드 가져오기
            original_attr = helpers.__getattribute__(name)

            if callable(original_attr):
                # 워크플로우 추적 래퍼 적용
                return self._workflow_tracked(original_attr, name)
            else:
                return original_attr
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _workflow_tracked(self, func, func_name):
        """워크플로우 추적 데코레이터"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 사용법 표시
            self._show_usage_once(func_name)

            # 실행 시작
            start_time = time.time()

            try:
                # 함수 실행
                result = func(*args, **kwargs)

                # 성공 기록
                self._log_execution(func_name, "success", time.time() - start_time)

                return result

            except Exception as e:
                # 실패 기록
                self._log_execution(func_name, "error", time.time() - start_time, str(e))
                raise

        return wrapper

    def _show_usage_once(self, func_name: str):
        """함수별로 한 번만 사용법 표시"""
        if func_name not in self._usage_shown:
            self._usage_shown.add(func_name)
            usage = self._get_usage(func_name)
            if usage:
                print(f"💡 {func_name} 사용법: {usage}")

    def _get_usage(self, func_name: str) -> Optional[str]:
        """함수별 사용법 가이드"""
        usage_guide = {
            "read_file": "파일 읽기 - read_file('경로')",
            "create_file": "파일 생성 - create_file('경로', '내용')",
            "search_files": "파일 검색 - search_files('경로', '패턴')",
            "git_status": "Git 상태 - git_status()",
            "flow_project": "프로젝트 전환 - flow_project('프로젝트명')",
            "build_project_context": "프로젝트 컨텍스트 생성 - build_project_context()",
            "update_context": "컨텍스트 업데이트 - update_context('키', 값)"
        }
        return usage_guide.get(func_name)

    def _log_execution(self, func_name: str, status: str, duration: float, error: str = None):
        """함수 실행 로그"""
        if self._current_task:
            log_entry = {
                "function": func_name,
                "status": status,
                "duration": f"{duration:.3f}s",
                "timestamp": datetime.now().isoformat()
            }
            if error:
                log_entry["error"] = error

            # 현재 태스크에 로그 추가
            self._add_task_note(f"[{status}] {func_name} ({duration:.3f}s)")

    def _add_task_note(self, note: str):
        """현재 태스크에 노트 추가"""
        if self.workflow_integration and self._current_task:
            try:
                self.workflow_integration.update_task(
                    self._current_task['id'],
                    {'notes': [note]}
                )
            except:
                pass

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

            self.workflow_integration.update_task(task['id'], updates)
            print(f"✅ 태스크 상태 업데이트: {status}")

    def show_workflow_status(self):
        """워크플로우 상태 표시"""
        workflow = self.get_current_workflow()
        if workflow['plan']:
            plan = workflow['plan']
            print(f"\n📋 현재 워크플로우: {plan['name']}")
            print(f"진행률: {workflow['progress']:.1f}%")

            # 현재 태스크
            current = self.get_current_task()
            if current:
                print(f"현재 작업: {current['title']}")
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

        # 에러 발생 시에도 False 반환하여 에러 전파
        return False


# 기존 helpers import
try:
    from ..unified_ai_helpers import UnifiedHelpers
    helpers = UnifiedHelpers()
except:
    # 폴백
    class DummyHelpers:
        pass
    helpers = DummyHelpers()

# 전역 인스턴스 생성
workflow_helpers = WorkflowAwareHelpers()
