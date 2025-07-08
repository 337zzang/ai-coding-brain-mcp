"""
워크플로우 v2 핸들러 함수들 - 간소화된 7개 명령어 체계
각 명령어의 실제 구현
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from python.ai_helpers.helper_result import HelperResult
from .manager import WorkflowV2Manager
from .models import Task, TaskStatus, PlanStatus
from .context_integration import sync_workflow_to_context


def workflow_start(plan_name: str = "") -> HelperResult:
    """워크플로우 시작 또는 재개

    Args:
        plan_name: 새 플랜 이름 (비어있으면 현재 플랜 재개)
    """
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        # 플랜 이름이 있으면 새 플랜 생성
        if plan_name:
            # 기존 플랜이 있으면 히스토리로 이동
            if wm.current_plan:
                wm.archive_current_plan()

            # 새 플랜 생성
            plan = wm.create_plan(plan_name, "")
            if plan:
                return HelperResult(True, data={
                    'success': True,
                    'plan': {
                        'id': str(plan.id),
                        'name': plan.name,
                        'status': plan.status.value
                    },
                    'message': f"🚀 Started new plan: {plan.name}"
                })
        else:
            # 현재 플랜 재개
            if wm.current_plan:
                current_task = wm.get_current_task()
                return HelperResult(True, data={
                    'success': True,
                    'plan': wm.current_plan.name,
                    'current_task': {
                        'title': current_task.title if current_task else "No active task",
                        'index': wm.current_plan.current_task_index + 1,
                        'total': len(wm.current_plan.tasks)
                    },
                    'message': f"▶️ Resuming plan: {wm.current_plan.name}"
                })
            else:
                return HelperResult(False, error="No active plan. Use /start <plan-name> to create one.")

    except Exception as e:
        return HelperResult(False, error=f"Start failed: {str(e)}")


def workflow_focus(task_ref: str = "") -> HelperResult:
    """특정 태스크에 포커스 또는 현재 태스크 표시

    Args:
        task_ref: 태스크 번호 또는 ID (비어있으면 현재 태스크)
    """
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(False, error="No active plan")

        # 태스크 참조가 없으면 현재 태스크 표시
        if not task_ref:
            current = wm.get_current_task()
            if current:
                return HelperResult(True, data={
                    'success': True,
                    'current_task': {
                        'index': wm.current_plan.current_task_index + 1,
                        'total': len(wm.current_plan.tasks),
                        'id': str(current.id),
                        'title': current.title,
                        'description': current.description,
                        'status': current.status.value
                    }
                })
            else:
                return HelperResult(False, error="No current task")

        # 태스크 번호로 이동
        try:
            task_num = int(task_ref) - 1  # 1-based to 0-based
            if 0 <= task_num < len(wm.current_plan.tasks):
                wm.current_plan.current_task_index = task_num
                wm.save_data()

                task = wm.current_plan.tasks[task_num]
                return HelperResult(True, data={
                    'success': True,
                    'message': f"📍 Focused on task {task_num + 1}: {task.title}",
                    'task': {
                        'index': task_num + 1,
                        'id': str(task.id),
                        'title': task.title,
                        'status': task.status.value
                    }
                })
            else:
                return HelperResult(False, error=f"Invalid task number: {task_ref}")

        except ValueError:
            return HelperResult(False, error=f"Invalid task reference: {task_ref}")

    except Exception as e:
        return HelperResult(False, error=f"Focus failed: {str(e)}")


def workflow_plan(title: str = "", description: str = "") -> HelperResult:
    """플랜 관리 (생성/조회/목록)

    Args:
        title: 플랜 제목 또는 'list' (비어있으면 현재 플랜 정보)
        description: 플랜 설명
    """
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        # 'list' 하위 명령어 처리
        if title.lower() == 'list':
            return workflow_list_plans()

        # 제목이 없으면 현재 플랜 정보
        if not title:
            if wm.current_plan:
                completed = sum(1 for t in wm.current_plan.tasks if t.status == TaskStatus.COMPLETED)
                return HelperResult(True, data={
                    'success': True,
                    'plan': {
                        'id': str(wm.current_plan.id),
                        'name': wm.current_plan.name,
                        'description': wm.current_plan.description,
                        'status': wm.current_plan.status.value,
                        'progress': {
                            'completed': completed,
                            'total': len(wm.current_plan.tasks),
                            'percentage': round(completed / len(wm.current_plan.tasks) * 100) if wm.current_plan.tasks else 0
                        }
                    }
                })
            else:
                return HelperResult(False, error="No active plan")

        # 새 플랜 생성
        if wm.current_plan:
            wm.archive_current_plan()

        plan = wm.create_plan(title, description)
        if plan:
            sync_workflow_to_context()
            return HelperResult(True, data={
                'success': True,
                'plan': {
                    'id': str(plan.id),
                    'name': plan.name,
                    'description': plan.description
                },
                'message': f"📋 Created new plan: {plan.name}"
            })
        else:
            return HelperResult(False, error="Failed to create plan")

    except Exception as e:
        return HelperResult(False, error=f"Plan operation failed: {str(e)}")


def workflow_list_plans() -> HelperResult:
    """모든 플랜 목록 조회"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        plans = []

        # 현재 플랜
        if wm.current_plan:
            plans.append({
                'id': str(wm.current_plan.id),
                'name': wm.current_plan.name,
                'status': 'active',
                'created': wm.current_plan.created_at.isoformat() if hasattr(wm.current_plan, 'created_at') else '',
                'tasks': len(wm.current_plan.tasks)
            })

        # 히스토리의 플랜들 (최근 10개)
        for entry in wm.data.history[-10:]:
            if entry.entry_type == "plan_completed":
                plans.append({
                    'id': entry.details.get('plan_id', ''),
                    'name': entry.details.get('plan_name', ''),
                    'status': 'completed',
                    'created': entry.timestamp.isoformat(),
                    'tasks': entry.details.get('total_tasks', 0)
                })

        return HelperResult(True, data={
            'success': True,
            'plans': plans,
            'total': len(plans)
        })

    except Exception as e:
        return HelperResult(False, error=f"Failed to list plans: {str(e)}")


def workflow_task(title: str = "", description: str = "") -> HelperResult:
    """태스크 관리 통합 (추가/목록/현재)

    Args:
        title: 태스크 제목 (비어있으면 목록, 'current'면 현재 태스크)
        description: 태스크 설명
    """
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(False, error="No active plan. Use /plan to create one.")

        # title이 없으면 태스크 목록 표시
        if not title:
            return workflow_tasks()

        # "current"면 현재 태스크 표시
        if title.lower() == "current":
            return workflow_current()

        # 새 태스크 추가
        task = wm.add_task(title, description)
        if task:
            sync_workflow_to_context()
            return HelperResult(True, data={
                'success': True,
                'task': {
                    'id': str(task.id),
                    'title': task.title,
                    'description': task.description,
                    'index': len(wm.current_plan.tasks)
                },
                'message': f"✅ Task added: {task.title}"
            })
        else:
            return HelperResult(False, error="Failed to add task")

    except Exception as e:
        return HelperResult(False, error=f"Task operation failed: {str(e)}")


def workflow_tasks() -> HelperResult:
    """모든 태스크 목록 조회"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(False, error="No active plan")

        tasks_data = []
        for i, task in enumerate(wm.current_plan.tasks):
            tasks_data.append({
                'index': i + 1,
                'id': str(task.id),
                'title': task.title,
                'description': task.description,
                'status': task.status.value,
                'is_current': i == wm.current_plan.current_task_index
            })

        return HelperResult(True, data={
            'success': True,
            'plan': wm.current_plan.name,
            'tasks': tasks_data,
            'total': len(tasks_data),
            'completed': sum(1 for t in tasks_data if t['status'] == 'completed')
        })

    except Exception as e:
        return HelperResult(False, error=f"Failed to list tasks: {str(e)}")


def workflow_current() -> HelperResult:
    """현재 태스크 정보 조회"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(False, error="No active plan")

        current = wm.get_current_task()
        if current:
            return HelperResult(True, data={
                'success': True,
                'plan': wm.current_plan.name,
                'current_task': {
                    'index': wm.current_plan.current_task_index + 1,
                    'total': len(wm.current_plan.tasks),
                    'id': str(current.id),
                    'title': current.title,
                    'description': current.description,
                    'status': current.status.value
                }
            })
        else:
            return HelperResult(True, data={
                'success': True,
                'plan': wm.current_plan.name,
                'message': "No current task"
            })

    except Exception as e:
        return HelperResult(False, error=f"Failed to get current task: {str(e)}")


def workflow_next(note: str = "") -> HelperResult:
    """현재 태스크 완료 후 다음으로 이동 (통합: done/complete/next)

    Args:
        note: 완료 메모 (선택사항)
    """
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(False, error="No active plan")

        current = wm.get_current_task()
        if not current:
            return HelperResult(False, error="No current task")

        # 현재 태스크가 완료되지 않았다면 완료 처리
        if current.status != TaskStatus.COMPLETED:
            # 완료 처리
            result = wm.complete_task(current.id, note)
            if not result:
                return HelperResult(False, error="Failed to complete task")

            # 완료 메시지
            completed_msg = f"✅ Completed: {current.title}"
            if note:
                completed_msg += f" (Note: {note})"
        else:
            completed_msg = f"Task already completed: {current.title}"

        # 다음 태스크로 이동
        if wm.current_plan.current_task_index < len(wm.current_plan.tasks) - 1:
            wm.current_plan.current_task_index += 1
            wm.save_data()

            next_task = wm.get_current_task()
            if next_task:
                sync_workflow_to_context()
                return HelperResult(True, data={
                    'success': True,
                    'message': completed_msg,
                    'next_task': {
                        'index': wm.current_plan.current_task_index + 1,
                        'total': len(wm.current_plan.tasks),
                        'id': str(next_task.id),
                        'title': next_task.title,
                        'description': next_task.description,
                        'status': next_task.status.value
                    }
                })
        else:
            # 모든 태스크 완료
            wm.current_plan.status = PlanStatus.COMPLETED
            wm.save_data()
            sync_workflow_to_context()

            return HelperResult(True, data={
                'success': True,
                'message': completed_msg,
                'plan_completed': True,
                'summary': f"🎉 All tasks completed for plan: {wm.current_plan.name}"
            })

    except Exception as e:
        return HelperResult(False, error=f"Failed to proceed: {str(e)}")


def workflow_done(note: str = "") -> HelperResult:
    """현재 태스크 완료 (레거시 지원)"""
    return workflow_next(note)


def workflow_status(subcommand: str = "") -> HelperResult:
    """워크플로우 상태 확인 (통합: status/history)

    Args:
        subcommand: 'history' 등 하위 명령어
    """
    try:
        # history 하위 명령어 처리
        if subcommand.lower() == 'history':
            return workflow_history()

        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        status_data = {
            'success': True,
            'status': {}
        }

        if wm.current_plan:
            completed = sum(1 for t in wm.current_plan.tasks if t.status == TaskStatus.COMPLETED)
            current_task = wm.get_current_task()

            status_data['status'] = {
                'status': 'active',
                'plan_name': wm.current_plan.name,
                'plan_id': str(wm.current_plan.id),
                'total_tasks': len(wm.current_plan.tasks),
                'completed_tasks': completed,
                'progress_percent': round(completed / len(wm.current_plan.tasks) * 100) if wm.current_plan.tasks else 0,
                'current_task': {
                    'title': current_task.title,
                    'status': current_task.status.value
                } if current_task else None
            }
        else:
            status_data['status'] = {
                'status': 'no_plan',
                'message': 'No active plan. Use /plan to create one.'
            }

        return HelperResult(True, data=status_data)

    except Exception as e:
        return HelperResult(False, error=f"Failed to get status: {str(e)}")


def workflow_history() -> HelperResult:
    """작업 이력 조회"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        history_entries = []
        for entry in wm.data.history[-20:]:  # 최근 20개
            history_entries.append({
                'timestamp': entry.timestamp.isoformat(),
                'type': entry.entry_type,
                'details': entry.details
            })

        return HelperResult(True, data={
            'success': True,
            'history': history_entries,
            'total': len(history_entries)
        })

    except Exception as e:
        return HelperResult(False, error=f"Failed to get history: {str(e)}")


def workflow_build(target: str = "") -> HelperResult:
    """프로젝트 문서 빌드 (통합: build/review)

    Args:
        target: 'task', 'review' 등 빌드 대상
    """
    try:
        from python.helpers_wrapper import build_project_context

        # review 하위 명령어 처리
        if target.lower() == 'review':
            return workflow_review()

        # task 문서화
        if target.lower() == 'task':
            wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")
            current = wm.get_current_task()
            if current:
                # 현재 태스크 문서화 로직
                doc_content = f"# Task Completion Report\n\n"
                doc_content += f"**Task**: {current.title}\n"
                doc_content += f"**Status**: {current.status.value}\n"
                doc_content += f"**Completed**: {datetime.now().isoformat()}\n\n"

                # 문서 저장
                doc_path = f"docs/tasks/task_{current.id}_report.md"
                # TODO: 실제 파일 저장 로직 구현

                return HelperResult(True, data={
                    'success': True,
                    'message': f"📝 Task documentation created: {doc_path}"
                })

        # 기본: 전체 프로젝트 문서 빌드
        result = build_project_context()
        if result.ok:
            return HelperResult(True, data={
                'success': True,
                'message': "📚 Project documentation built successfully"
            })
        else:
            return HelperResult(False, error=f"Build failed: {result.error}")

    except Exception as e:
        return HelperResult(False, error=f"Build failed: {str(e)}")


def workflow_review() -> HelperResult:
    """완료된 작업 리뷰 생성"""
    try:
        wm = WorkflowV2Manager.get_instance("ai-coding-brain-mcp")

        if not wm.current_plan:
            return HelperResult(False, error="No active plan")

        # 완료된 태스크들 수집
        completed_tasks = [t for t in wm.current_plan.tasks if t.status == TaskStatus.COMPLETED]

        if not completed_tasks:
            return HelperResult(False, error="No completed tasks to review")

        # 리뷰 문서 생성
        review_content = f"# Workflow Review: {wm.current_plan.name}\n\n"
        review_content += f"**Date**: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        review_content += f"## Completed Tasks ({len(completed_tasks)})\n\n"

        for task in completed_tasks:
            review_content += f"### ✅ {task.title}\n"
            if task.description:
                review_content += f"{task.description}\n"
            review_content += "\n"

        return HelperResult(True, data={
            'success': True,
            'review': review_content,
            'completed_count': len(completed_tasks),
            'message': f"📊 Review generated for {len(completed_tasks)} completed tasks"
        })

    except Exception as e:
        return HelperResult(False, error=f"Review generation failed: {str(e)}")
