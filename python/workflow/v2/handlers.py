"""
워크플로우 v2 핸들러 - 완전히 독립적인 구현
"""

from typing import List, Dict, Optional
from python.ai_helpers.helper_result import HelperResult
from python.core.context_manager import get_context_manager
from .manager import WorkflowV2Manager
from .models import WorkflowPlan, Task, TaskStatus
from datetime import datetime
import os

# ===== 프로젝트 관리 =====

def get_manager() -> WorkflowV2Manager:
    """현재 프로젝트의 WorkflowV2Manager 인스턴스 반환 (캐시됨)"""
    try:
        from core.context_manager import get_context_manager
        context_manager = get_context_manager()
        project_name = context_manager.current_project
    except:
        project_name = "ai-coding-brain-mcp"  # 기본값

    # 최적화된 인스턴스 반환
    return WorkflowV2Manager.get_instance(project_name)



def workflow_start(project_name: str, description: str = "") -> HelperResult:
    """새 프로젝트 생성 및 전환"""
    try:
        # 프로젝트 디렉토리 생성
        project_path = os.path.join(os.getcwd(), project_name)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            os.makedirs(os.path.join(project_path, 'memory'), exist_ok=True)

            # 기본 파일 생성
            readme = f"# {project_name}\n\n{description}"
            with open(os.path.join(project_path, 'README.md'), 'w') as f:
                f.write(readme)

        # 프로젝트로 이동
        os.chdir(project_path)

        # 컨텍스트 매니저 업데이트
        cm = get_context_manager()
        cm.switch_project(project_name)

        return HelperResult(True, data={
            'success': True,
            'message': f'✅ 프로젝트 생성 및 전환: {project_name}',
            'path': project_path
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

def workflow_focus(project_name: str) -> HelperResult:
    """기존 프로젝트로 전환"""
    try:
        # flow_project와 유사한 기능
        project_path = os.path.join(os.path.dirname(os.getcwd()), project_name)
        if not os.path.exists(project_path):
            return HelperResult(False, error=f"Project not found: {project_name}")

        os.chdir(project_path)

        # 컨텍스트 매니저 업데이트
        cm = get_context_manager()
        cm.switch_project(project_name)

        # 워크플로우 인스턴스 생성 (자동 로드)
        wm = WorkflowV2Manager.get_instance(project_name)

        return HelperResult(True, data={
            'success': True,
            'message': f'✅ 프로젝트 전환: {project_name}',
            'path': project_path
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

# ===== 플랜 관리 =====

def workflow_plan(name: str, description: str = "", reset: bool = False) -> HelperResult:
    """새 플랜 생성"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        # 리셋 옵션 처리
        if reset and wm.current_plan:
            print(f"📦 이전 플랜 '{wm.current_plan.name}'이(가) 히스토리로 이동되었습니다.")

        plan = wm.create_plan(name, description, reset)
        print(f"✨ 새 플랜 생성: {name}")

        return HelperResult(True, data={
            'success': True,
            'message': f'새 계획 생성됨: {name}',
            'plan_id': plan.id,
            'reset': reset
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

def workflow_list_plans() -> HelperResult:
    """플랜 목록 조회"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")
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

        # 히스토리
        for plan_dict in wm.history:
            plans.append({
                'id': plan_dict.get('id'),
                'name': plan_dict.get('name'),
                'status': 'completed',
                'created': plan_dict.get('created_at'),
                'completed': plan_dict.get('completed_at'),
                'tasks': len(plan_dict.get('tasks', []))
            })

        return HelperResult(True, data={
            'success': True,
            'plans': plans,
            'total': len(plans)
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

# ===== 태스크 관리 =====

def workflow_task(title: str, description: str = "") -> HelperResult:
    """태스크 추가"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(False, error="No active plan. Create a plan first.")

        task = wm.add_task(title, description)
        if not task:
            return HelperResult(False, error="Failed to add task")

        return HelperResult(True, data={
            'success': True,
            'message': f'작업 추가됨: {title}',
            'task_id': task.id,
            'request_plan': True
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

def workflow_tasks() -> HelperResult:
    """태스크 목록 조회"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(True, data={
                'success': True,
                'tasks': [],
                'message': 'No active plan'
            })

        tasks = []
        for i, task in enumerate(wm.get_tasks()):
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

def workflow_current() -> HelperResult:
    """현재 태스크 정보"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")
        task = wm.get_current_task()

        if not task:
            return HelperResult(True, data={
                'success': True,
                'message': 'No current task',
                'current_task': None
            })

        return HelperResult(True, data={
            'success': True,
            'plan': wm.current_plan.name,
            'current_task': {
                'index': wm.current_plan.current_task_index + 1,
                'total': len(wm.current_plan.tasks),
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status.value
            }
        })

    except Exception as e:
        return HelperResult(False, error=str(e))

def workflow_next() -> HelperResult:
    """다음 태스크로 이동"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(False, error="No active plan")

        current = wm.get_current_task()
        if current and current.status != TaskStatus.COMPLETED:
            return HelperResult(False, error="Current task not completed. Use /done first.")

        # 다음 태스크로 이동
        if wm.current_plan.current_task_index < len(wm.current_plan.tasks) - 1:
            wm.current_plan.current_task_index += 1
            wm.save_data()

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

def workflow_done(notes: str = "", details: List[str] = None) -> HelperResult:
    """현재 태스크 완료"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")
        current = wm.get_current_task()

        if not current:
            return HelperResult(False, error="No current task to complete")

        # 태스크 완료
        result = wm.complete_current_task(notes)

        if result:
            data = {
                'success': True,
                'message': f'✅ 작업 완료: {current.title}',
                'task_id': current.id,
                'notes': notes
            }

            # 모든 태스크 완료 확인
            if wm.current_plan.status == 'completed':
                data['all_completed'] = True
                data['plan_completed'] = True

            return HelperResult(True, data=data)
        else:
            return HelperResult(False, error="Failed to complete task")

    except Exception as e:
        return HelperResult(False, error=str(e))

# ===== 상태 조회 =====

def workflow_status() -> HelperResult:
    """전체 워크플로우 상태"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")
        status = wm.get_status()

        # 현재 태스크 정보 추가
        current_task = wm.get_current_task()
        if current_task:
            status['current_task'] = {
                'title': current_task.title,
                'status': current_task.status.value
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
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")
        history = []

        # 현재 플랜의 완료된 태스크
        if wm.current_plan:
            for task in wm.current_plan.tasks:
                if task.status == TaskStatus.COMPLETED:
                    history.append({
                        'type': 'task',
                        'title': task.title,
                        'completed_at': task.completed_at,
                        'plan': wm.current_plan.name
                    })

        # 히스토리 플랜들
        for plan_dict in wm.history:
            history.append({
                'type': 'plan',
                'title': plan_dict.get('name'),
                'completed_at': plan_dict.get('completed_at'),
                'tasks_count': len(plan_dict.get('tasks', []))
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

# ===== 확장 기능 =====

def workflow_build(update_readme: bool = True) -> HelperResult:
    """프로젝트 문서 빌드"""
    try:
        # TODO: 실제 빌드 로직 구현
        return HelperResult(True, data={
            'success': True,
            'message': 'Build functionality to be implemented',
            'request_build': True
        })
    except Exception as e:
        return HelperResult(False, error=str(e))

def workflow_review(scope: str = "current") -> HelperResult:
    """코드/작업 리뷰"""
    try:
        # TODO: 실제 리뷰 로직 구현
        return HelperResult(True, data={
            'success': True,
            'message': 'Review functionality to be implemented',
            'scope': scope
        })
    except Exception as e:
        return HelperResult(False, error=str(e))

# Export all
__all__ = [
    'workflow_start', 'workflow_focus',
    'workflow_plan', 'workflow_list_plans',
    'workflow_task', 'workflow_tasks', 'workflow_current', 'workflow_next', 'workflow_done',
    'workflow_status', 'workflow_history',
    'workflow_build', 'workflow_review'
]
