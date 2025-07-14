
"""
통합 워크플로우 시스템 - 최종 통일 버전
레거시 시스템을 완전히 대체하는 단일 통합 시스템
"""

import sys
import os
sys.path.append('./python')

from ai_helpers.workflow.workflow_adapter import WorkflowAdapter
from ai_helpers.workflow.integrated_workflow import IntegratedWorkflowManager
from ai_helpers.protocols.stdout_protocol import StdoutProtocol

# 전역 어댑터 (싱글톤)
_workflow_adapter = None

def get_adapter():
    """전역 워크플로우 어댑터 반환"""
    global _workflow_adapter
    if _workflow_adapter is None:
        _workflow_adapter = WorkflowAdapter()
    return _workflow_adapter

# ============= 통합 워크플로우 클래스 =============

class UnifiedWorkflow:
    """통합 워크플로우 시스템 - 모든 워크플로우 기능을 제공"""

    def __init__(self):
        self.adapter = get_adapter()

    def flow_project(self, project_name):
        """프로젝트 전환"""
        return self.adapter.flow_project(project_name)

    def create_plan(self, plan_name, tasks):
        """워크플로우 계획 생성"""
        if not self.adapter.current_project:
            self.adapter.flow_project('default_project')
        return self.adapter.create_workflow_plan(plan_name, tasks)

    def execute_task(self, task):
        """작업 실행"""
        return self.adapter.execute_workflow_task(task)

    def get_status(self):
        """상태 조회"""
        return self.adapter.get_workflow_status()

    def checkpoint(self, name, data):
        """체크포인트 생성"""
        return self.adapter.checkpoint(name, data)

    def next_action(self, action, params=None):
        """다음 작업 지시"""
        return self.adapter.next_action(action, params or {})

    def get_history(self):
        """실행 히스토리 조회"""
        return self.adapter.get_execution_history()

    # 추가 유틸리티 메서드
    def create_and_execute(self, plan_name, tasks):
        """워크플로우 생성 후 즉시 실행"""
        plan = self.create_plan(plan_name, tasks)
        if not plan.get('success'):
            return {'error': 'Failed to create plan'}

        results = []
        for task in tasks:
            result = self.execute_task(task)
            results.append(result)

            # 자동 체크포인트
            self.checkpoint(f"auto_{task['id']}", result)

        return {
            'plan_id': plan.get('plan_id'),
            'results': results,
            'summary': {
                'total': len(tasks),
                'success': sum(1 for r in results if r.get('status') == 'success'),
                'failed': sum(1 for r in results if r.get('status') == 'error')
            }
        }

    def quick_task(self, title, task_type='general', **kwargs):
        """빠른 단일 작업 실행"""
        task = {
            'id': f"quick_{int(time.time())}",
            'title': title,
            'type': task_type,
            **kwargs
        }

        plan = self.create_plan(f"Quick: {title}", [task])
        if plan.get('success'):
            return self.execute_task(task)
        return {'error': 'Failed to create quick task'}

# ============= Helpers 통합 =============

def setup_unified_workflow(helpers_obj):
    """Helpers에 통합 워크플로우 시스템 설정"""

    # 기존 메서드 정리
    legacy_methods = ['_original_workflow', '_original_flow_project', 
                      'workflow_create_plan', 'workflow_execute_task',
                      'workflow_get_status', 'workflow_checkpoint',
                      'workflow_next_action', 'workflow_flow_project']

    for method in legacy_methods:
        if hasattr(helpers_obj, method):
            delattr(helpers_obj, method)

    # 통합 워크플로우 객체 생성
    unified = UnifiedWorkflow()

    # workflow 속성으로 설정
    setattr(helpers_obj, 'workflow', unified)

    # 직접 메서드도 추가 (선택적 사용)
    setattr(helpers_obj, 'create_workflow', unified.create_plan)
    setattr(helpers_obj, 'execute_task', unified.execute_task)
    setattr(helpers_obj, 'workflow_status', unified.get_status)

    # Task 관련 기존 메서드 통합
    if hasattr(helpers_obj, 'quick_task'):
        helpers_obj._original_quick_task = helpers_obj.quick_task
    setattr(helpers_obj, 'quick_task', unified.quick_task)

    print("✅ 통합 워크플로우 시스템 설정 완료")
    print("  - helpers.workflow: 모든 워크플로우 기능")
    print("  - helpers.create_workflow: 워크플로우 생성")
    print("  - helpers.execute_task: 작업 실행")
    print("  - helpers.quick_task: 빠른 작업 실행")

    return unified

# ============= 자동 초기화 =============

if __name__ == "__main__":
    print("✅ 통합 워크플로우 시스템 로드됨")
