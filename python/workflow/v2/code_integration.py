
# workflow_code_integration.py - 코드 실행과 워크플로우 연계

from typing import Optional, Dict, Any
from datetime import datetime
from python.workflow.v2.manager import WorkflowV2Manager
from python.workflow.v2.context_integration import ContextIntegration

class WorkflowCodeIntegration:
    """코드 실행과 워크플로우를 연계하는 통합 클래스"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.manager = WorkflowV2Manager(project_name)
        self.context = ContextIntegration()

    def get_current_task_context(self) -> Optional[Dict[str, Any]]:
        """현재 진행 중인 태스크 정보 반환"""
        # manager의 data 속성 직접 접근
        self.manager.load_data()
        current_plan = self.manager.data.get('current_plan') if hasattr(self.manager, 'data') else None

        if not current_plan:
            return None

        # 진행 중인 태스크 찾기
        for task in current_plan.get('tasks', []):
            if task.get('status') == 'in_progress':
                return {
                    'task_id': task.get('id'),
                    'task_title': task.get('title'),
                    'plan_name': current_plan.get('name'),
                    'plan_id': current_plan.get('id')
                }

        return None

    def record_code_execution(self, code: str, result: Dict[str, Any], 
                            execution_time: float) -> bool:
        """코드 실행 결과를 워크플로우에 기록"""
        current_task = self.get_current_task_context()

        if not current_task:
            return False

        # 실행 기록 생성
        execution_record = {
            'timestamp': datetime.now().isoformat(),
            'task_id': current_task['task_id'],
            'task_title': current_task['task_title'],
            'code_snippet': code[:200] + '...' if len(code) > 200 else code,
            'success': result.get('success', False),
            'execution_time': execution_time,
            'output_lines': len(result.get('output', '').split('\n')),
            'error': result.get('error', None)
        }

        # 컨텍스트에 기록
        self.context.record_event(
            'code_execution',
            f"Executed code for task: {current_task['task_title']}",
            execution_record
        )

        return True

    def should_auto_progress(self, result: Dict[str, Any]) -> bool:
        """실행 결과에 따라 태스크 자동 진행 여부 결정"""
        # 성공적으로 실행되고 특정 키워드가 포함된 경우
        if result.get('success'):
            output = result.get('output', '').lower()
            completion_keywords = ['완료', 'complete', 'done', 'finished', '성공']

            return any(keyword in output for keyword in completion_keywords)

        return False

    def auto_progress_task(self, completion_note: str = "") -> Dict[str, Any]:
        """현재 태스크를 자동으로 완료 처리"""
        from python.workflow.v2.dispatcher import WorkflowDispatcher

        dispatcher = WorkflowDispatcher(self.project_name)

        # /next 명령 실행
        completion_message = f"자동 완료: {completion_note}" if completion_note else "코드 실행 완료"
        return dispatcher.execute_command(f"/next {completion_message}")


# 헬퍼 함수 추가 (helpers_wrapper.py에 추가될 내용)
def execute_code_with_workflow(code: str, auto_progress: bool = False) -> Dict[str, Any]:
    """워크플로우와 연계된 코드 실행"""
    import time
    from python.helpers_wrapper import execute_code

    # 프로젝트 이름 가져오기
    project_name = helpers.get_project_name().get_data('unknown')

    # 워크플로우 통합 객체 생성
    integration = WorkflowCodeIntegration(project_name)

    # 현재 태스크 확인
    current_task = integration.get_current_task_context()
    if current_task:
        print(f"🎯 현재 태스크: {current_task['task_title']}")

    # 코드 실행
    start_time = time.time()
    result = execute_code(code)
    execution_time = time.time() - start_time

    # 실행 결과 기록
    if current_task:
        integration.record_code_execution(code, result, execution_time)

        # 자동 진행 확인
        if auto_progress and integration.should_auto_progress(result):
            progress_result = integration.auto_progress_task("코드 실행 성공")
            print(f"✅ 태스크 자동 완료: {progress_result.get('message')}")

    return result
