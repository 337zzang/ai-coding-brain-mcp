#!/usr/bin/env python3
"""
개선된 작업(Task) 관리 명령어
ProjectContext와 dict 모두 지원하는 유연한 구조
"""

import os
from typing import Dict, Any, Optional, List

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.context_manager import get_context_manager
from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse
from core.models import TaskStatus
from commands.plan import get_plan, set_plan, plan_to_dict
from analyzers.project_analyzer import ProjectAnalyzer

# 파일 검색을 위한 헬퍼 함수들 직접 import
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from json_repl_session import AIHelpers
    file_helpers = AIHelpers()
except Exception as e:
    file_helpers = None


def get_current_task(context) -> Optional[str]:
    """현재 작업 ID 가져오기"""
    if hasattr(context, 'current_task'):
        return context.current_task
    elif isinstance(context, dict):
        return context.get('current_task')
    return None


def set_current_task(context, task_id: Optional[str]):
    """현재 작업 설정"""
    if hasattr(context, 'current_task'):
        context.current_task = task_id
    elif isinstance(context, dict):
        context['current_task'] = task_id


def get_tasks(context) -> Dict[str, List]:
    """작업 목록 가져오기"""
    if hasattr(context, 'tasks'):
        return context.tasks
    elif isinstance(context, dict):
        return context.get('tasks', {})
    return {}


def update_plan_in_context(context, plan_dict: Dict):
    """수정된 plan을 context에 반영"""
    return set_plan(context, plan_dict)


def cmd_task(action: str, *args) -> StandardResponse:
    """작업 관리 명령어
    
    Args:
        action: 작업 동작 (list, add, done, remove)
        args: 추가 인자
        
    Returns:
        StandardResponse: 표준 응답
    """
    try:
        wm = get_workflow_manager()
    
        try:
            if action == 'list':
                # 작업 목록 표시
                status = wm.get_workflow_status()
                plan = wm.plan
            
                print(f"📋 계획: {plan.name}")
                # progress가 딕셔너리인 경우 처리
                progress_value = status.get('progress', 0)
                if isinstance(progress_value, dict):
                    progress_value = progress_value.get('value', 0)
                completed = status.get('completed_count', status.get('completed', 0))
                total = status.get('total_count', status.get('total', 0))
                print(f"진행률: {progress_value:.1f}% ({completed}/{total})")
            
                # Phase별 작업 표시
                for phase_id, phase in plan.phases.items():
                    phase_tasks = list(phase.tasks.values()) if hasattr(phase.tasks, 'values') else phase.tasks
                    if phase_tasks:
                        completed = len([t for t in phase_tasks if t.status == TaskStatus.COMPLETED])
                        print(f"\n{'✅' if completed == len(phase_tasks) else '🔄'} {phase.name} ({completed}/{len(phase_tasks)} 완료)")
                    
                        for task in phase_tasks:
                            icon = "✅" if task.status == TaskStatus.COMPLETED else ("🔄" if task.status == TaskStatus.IN_PROGRESS else "⏳")
                            print(f"   {icon} [{task.id}] {task.title}")
                            if task.status == TaskStatus.COMPLETED and hasattr(task, 'content') and task.content:
                                content_preview = task.content
                                print(f"      └─ 수행 내용: {content_preview}")
                            
                return StandardResponse(success=True, data=status)
            
            elif action == 'add' and len(args) >= 1:
                # 작업 추가 - content 필수
                # 사용법: task add <phase-id> <title> <content>
                
                if len(args) >= 2 and args[0].startswith('phase-'):
                    # 명시적으로 phase_id가 제공된 경우
                    phase_id = args[0]
                    if len(args) < 3:
                        return StandardResponse.error(
                            ErrorType.VALIDATION_ERROR,
                            "사용법: task add <phase-id> <title> <content>"
                        )
                    task_name = args[1]
                    content_text = args[2]  # content 필수
                else:
                    # phase_id가 없으면 현재 phase 사용
                    current_phase = wm.plan.current_phase if wm.plan else None
                    if not current_phase:
                        # Plan의 phase_order에서 첫 번째 phase 사용
                        if wm.plan and wm.plan.phase_order:
                            current_phase = wm.plan.phase_order[0]
                        else:
                            return StandardResponse.error(
                                ErrorType.VALIDATION_ERROR,
                                "현재 Phase가 설정되지 않았습니다"
                            )
                    
                    phase_id = current_phase
                    if len(args) < 2:
                        return StandardResponse.error(
                            ErrorType.VALIDATION_ERROR,
                            "사용법: task add <title> <content>"
                        )
                    task_name = args[0]
                    content_text = args[1]  # content 필수
                
                # add_task 호출 시 content 전달
                result = wm.add_task(
                    phase_id=phase_id,
                    title=task_name,
                    description=content_text[:100] + "..." if len(content_text) > 100 else content_text,  # 요약
                    content=content_text  # 전체 내용
                )
                
                if result.get('success'):
                    task = result['data']['task']
                    print(f"\n✅ 작업 추가됨: [{task.id}] {task.title}")
                    print(f"   Phase: {phase_id}")
                    print(f"   📝 내용: {content_text[:80]}...")
                
                return result
            
            elif action == 'done' and args:
                task_id = args[0]
                return wm.complete_task(task_id)
            
            else:
                from core.error_handler import ErrorType
                return StandardResponse.error(ErrorType.TASK_ERROR, f"잘못된 명령: {action}")
            
        except Exception as e:
            from core.error_handler import ErrorType
            return StandardResponse.error(ErrorType.TASK_ERROR, f"작업 처리 중 오류: {str(e)}")
    except Exception as e:
        logger.error(f"cmd_task 오류: {str(e)}")
        return StandardResponse.error(
            ErrorType.SYSTEM_ERROR,
            f"작업 관리 중 오류 발생: {str(e)}"
        )
if __name__ == "__main__":
    # 명령줄 인자 처리
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        args = sys.argv[2:]
        cmd_task(action, *args)
    else:
        cmd_task('list')
