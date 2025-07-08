"""
워크플로우 핸들러 함수들 - 새로운 함수형 API
각 함수는 독립적으로 동작하며 HelperResult를 반환
"""

from typing import List, Dict, Optional
from python.ai_helpers.helper_result import HelperResult
from python.workflow.workflow_manager import WorkflowManager
from python.workflow_integration import get_workflow_instance
from python.core.context_manager import get_context_manager
from datetime import datetime
import functools


def _save_workflow_data(wm):
    """v2: Plan 객체를 dict로 변환하여 저장"""
    try:
        # 데이터 준비
        data = {
            'version': '2.0',
            'current_plan': None,
            'history': []
        }

        # current_plan 변환
        if wm.current_plan:
            if hasattr(wm.current_plan, 'to_dict'):
                data['current_plan'] = wm.current_plan.to_dict()
            else:
                # Plan 객체가 아닌 경우 (이미 dict)
                data['current_plan'] = wm.current_plan

        # history 변환
        for plan in wm.history:
            if hasattr(plan, 'to_dict'):
                data['history'].append(plan.to_dict())
            else:
                data['history'].append(plan)

        # 파일에 저장
        import json
        import os

        workflow_path = os.path.join('memory', 'workflow.json')

        # 원자적 쓰기
        temp_path = workflow_path + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 원본 파일 교체
        if os.path.exists(workflow_path):
            os.remove(workflow_path)
        os.rename(temp_path, workflow_path)

        print("💾 워크플로우 저장 완료 (v2)")
        return True

    except Exception as e:
        print(f"❌ 워크플로우 저장 실패: {e}")
        return False


# 컨텍스트 자동 관리 데코레이터
def with_context_save(func):
    """함수 실행 후 자동으로 컨텍스트 저장"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 함수 실행
            result = func(*args, **kwargs)

            # 성공 시 자동 저장
            if result.ok:
                try:
                    # v2: 커스텀 save 사용
                    wm, _ = get_workflow_instance()
                    if wm:
                        _save_workflow_data(wm)

                    # 컨텍스트 업데이트
                    cm = get_context_manager()
                    cm.update_context('last_workflow_action', {
                        'command': func.__name__,
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    })
                except Exception as save_error:
                    # 저장 실패해도 결과는 반환
                    print(f"Warning: Auto-save failed: {save_error}")

            return result

        except Exception as e:
            return HelperResult(False, error=str(e))

    return wrapper

# 프로젝트 관리
@with_context_save
def workflow_start(project_name: str, description: str = "") -> HelperResult:
    """새 프로젝트 생성 및 전환"""
    try:
        from python.workflow.commands import WorkflowCommands
        cmd = WorkflowCommands()

        # 기존 handle_start 활용
        args = project_name
        if description:
            args = f"{project_name} | {description}"

        result = cmd.handle_start(args)

        if result.get('success'):
            return HelperResult(True, data=result)
        else:
            return HelperResult(False, error=result.get('error', 'Failed to start project'))

    except Exception as e:
        return HelperResult(False, error=str(e))

@with_context_save
def workflow_focus(project_name: str) -> HelperResult:
    """기존 프로젝트로 전환"""
    try:
        # flow_project와 동일한 기능
        from python.cmd_flow_project import flow_project
        return flow_project(project_name)

    except Exception as e:
        return HelperResult(False, error=str(e))

# 플랜 관리
@with_context_save
def workflow_plan(name: str, description: str = "", reset: bool = False) -> HelperResult:
    """새 플랜 생성"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용

        # reset 옵션 처리
        if reset and wm.current_plan:
            # 기존 플랜을 히스토리로 이동
            wm.history.append(wm.current_plan.to_dict() if hasattr(wm.current_plan, 'to_dict') else wm.current_plan)

        # 새 플랜 생성
        plan = wm.create_plan(name, description)

        return HelperResult(True, data={
            'success': True,
            'message': f'새 계획 생성됨: {name}',
            'plan_id': plan.id,
            'reset': reset
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

@with_context_save
def workflow_list_plans() -> HelperResult:
    """플랜 목록 조회"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용

        plans = []

        # 현재 플랜
        if wm.current_plan:
            plans.append({
                'id': wm.current_plan.id,
                'name': wm.current_plan.name,
                'status': 'active',
                'created': wm.current_plan.created_at,
                'tasks': len(wm.current_plan.tasks)
            })

        # 히스토리 플랜들
        for plan in wm.history:
            plans.append({
                'id': plan.id,
                'name': plan.name,
                'status': 'completed',
                'created': plan.created_at,
                'completed': plan.completed_at,
                'tasks': len(plan.tasks)
            })

        return HelperResult(True, data={
            'success': True,
            'plans': plans,
            'total': len(plans)
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

# 태스크 관리
@with_context_save
def workflow_task(title: str, description: str = "") -> HelperResult:
    """태스크 추가"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용

        if not wm.current_plan:
            return HelperResult(False, error="No active plan. Create a plan first.")

        task = wm.add_task(title, description)

        return HelperResult(True, data={
            'success': True,
            'message': f'작업 추가됨: {title}',
            'task_id': task.id,
            'request_plan': True  # AI 계획 수립 제안
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

@with_context_save
def workflow_tasks() -> HelperResult:
    """태스크 목록 조회"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용

        if not wm.current_plan:
            return HelperResult(True, data={
                'success': True,
                'tasks': [],
                'message': 'No active plan'
            })

        tasks = []
        for i, task in enumerate(wm.current_plan.tasks):
            tasks.append({
                'index': i + 1,
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status.value,
                'is_current': i == wm.current_plan.current_task_index
            })

        return HelperResult(True, data={
            'success': True,
            'plan': wm.current_plan.name,
            'tasks': tasks,
            'total_tasks': len(tasks),
            'current_index': wm.current_plan.current_task_index + 1
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

@with_context_save
def workflow_current() -> HelperResult:
    """현재 태스크 정보"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용
        task = wm.get_current_task()

        if not task:
            return HelperResult(True, data={
                'success': True,
                'message': 'No current task',
                'current_task': None
            })

        plan = wm.current_plan
        return HelperResult(True, data={
            'success': True,
            'plan': plan.name,
            'current_task': {
                'index': plan.current_task_index + 1,
                'total': len(plan.tasks),
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status.value
            }
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

@with_context_save
def workflow_next() -> HelperResult:
    """다음 태스크로 이동"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용

        if not wm.current_plan:
            return HelperResult(False, error="No active plan")

        # 현재 태스크가 완료되지 않았다면 경고
        current = wm.get_current_task()
        if current and current.status.value not in ['completed', 'skipped']:
            return HelperResult(False, error="Current task not completed. Use /done first.")

        # 다음 태스크로 이동
        if wm.current_plan.current_task_index < len(wm.current_plan.tasks) - 1:
            wm.current_plan.current_task_index += 1
            next_task = wm.get_current_task()

            return HelperResult(True, data={
                'success': True,
                'message': f'Moved to next task: {next_task.title}',
                'task': {
                    'id': next_task.id,
                    'title': next_task.title,
                    'description': next_task.description,
                    'index': wm.current_plan.current_task_index + 1
                }
            })
        else:
            return HelperResult(True, data={
                'success': True,
                'message': 'All tasks completed!',
                'all_completed': True
            })

    except Exception as e:
        return HelperResult(False, error=str(e))

@with_context_save
def workflow_done(notes: str = "", details: List[str] = None) -> HelperResult:
    """현재 태스크 완료"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용
        current = wm.get_current_task()

        if not current:
            return HelperResult(False, error="No current task to complete")

        # v2: 승인 과정 없이 바로 완료 처리
        # 태스크 상태를 직접 변경
        from python.workflow.models import TaskStatus
        current.status = TaskStatus.COMPLETED
        current.completed_at = datetime.now().isoformat()
        if notes:
            current.notes = notes

        # 다음 태스크로 이동
        plan = wm.current_plan
        if plan.current_task_index < len(plan.tasks) - 1:
            plan.current_task_index += 1
        else:
            # 모든 태스크 완료
            plan.status = 'completed'
            plan.completed_at = datetime.now().isoformat()

        # 저장
        wm.save_data()

        data = {
            'success': True,
            'message': f'✅ 작업 완료: {current.title}',
            'task_id': current.id,
            'notes': notes
        }

        if plan.status == 'completed':
            data['all_completed'] = True
            data['plan_completed'] = True

        return HelperResult(True, data=data)

    except Exception as e:
        return HelperResult(False, error=str(e))

def workflow_status() -> HelperResult:
    """전체 워크플로우 상태"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용
        cm = get_context_manager()

        status = {
            'project': cm.get_current_project_name(),
            'plan': None,
            'tasks': {
                'total': 0,
                'completed': 0,
                'progress': 0
            },
            'current_task': None
        }

        if wm.current_plan:
            completed = len([t for t in wm.current_plan.tasks if t.status.value == 'completed'])
            total = len(wm.current_plan.tasks)

            status['plan'] = {
                'id': wm.current_plan.id,
                'name': wm.current_plan.name,
                'status': 'active'
            }
            status['tasks'] = {
                'total': total,
                'completed': completed,
                'progress': (completed / total * 100) if total > 0 else 0
            }

            current = wm.get_current_task()
            if current:
                status['current_task'] = {
                    'title': current.title,
                    'status': current.status.value
                }

        return HelperResult(True, data={
            'success': True,
            'status': status
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

def workflow_history() -> HelperResult:
    """완료된 작업 이력"""
    try:
        wm, _ = get_workflow_instance()  # WorkflowManager만 사용

        history = []

        # 현재 플랜의 완료된 태스크들
        if wm.current_plan:
            for task in wm.current_plan.tasks:
                if task.status.value == 'completed':
                    history.append({
                        'type': 'task',
                        'title': task.title,
                        'completed_at': task.completed_at,
                        'plan': wm.current_plan.name
                    })

        # 완료된 플랜들
        for plan in wm.history:
            history.append({
                'type': 'plan',
                'title': plan.name,
                'completed_at': plan.completed_at,
                'tasks_count': len(plan.tasks)
            })

        # 시간순 정렬
        history.sort(key=lambda x: x.get('completed_at', ''), reverse=True)

        return HelperResult(True, data={
            'success': True,
            'history': history,
            'total': len(history)
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

# 확장 기능 (구현 예정)
def workflow_build(update_readme: bool = True) -> HelperResult:
    """프로젝트 문서 빌드"""
    return HelperResult(True, data={
        'success': True,
        'message': 'Build functionality will be implemented in Phase 4',
        'request_build': True
    })

def workflow_review(scope: str = "current") -> HelperResult:
    """코드/작업 리뷰 실행"""
    return HelperResult(True, data={
        'success': True,
        'message': 'Review functionality will be implemented in Phase 4',
        'scope': scope
    })

# 모든 함수 export
__all__ = [
    'workflow_start',
    'workflow_focus',
    'workflow_plan',
    'workflow_list_plans',
    'workflow_task',
    'workflow_tasks',
    'workflow_current',
    'workflow_next',
    'workflow_done',
    'workflow_status',
    'workflow_history',
    'workflow_build',
    'workflow_review',
    'with_context_save'
]
