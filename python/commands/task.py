#!/usr/bin/env python3
"""
작업(Task) 관리 명령어 - 안정화된 버전
모든 로직은 WorkflowManager로 위임하는 단순 래퍼
"""

import os
import sys
from typing import Optional, List
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse, ErrorType
from core.models import TaskStatus


def cmd_task(action: str, *args) -> StandardResponse:
    """작업(Task) 관리 - WorkflowManager로 위임하는 단순 래퍼
    
    Args:
        action: 수행할 작업 (list, add, done, remove, update)
        *args: action에 따른 추가 인자들
        
    Returns:
        StandardResponse: 표준 응답
    """
    try:
        wm = get_workflow_manager()
        
        # 계획이 없으면 오류
        if not wm.context.plan:
            return StandardResponse.error(
                ErrorType.PLAN_ERROR,
                "설정된 계획이 없습니다. 먼저 계획을 생성하세요."
            )
        
        # action별 처리
        if action == "list":
            # 작업 목록 조회
            phase_id = args[0] if args else None
            tasks = wm.list_tasks(phase_id)
            
            # 출력
            if phase_id:
                phase = wm.context.plan.phases.get(phase_id)
                if phase:
                    print(f"\n📋 {phase.name}의 작업 목록:")
                else:
                    return StandardResponse.error(
                        ErrorType.VALIDATION_ERROR,
                        f"Phase '{phase_id}'를 찾을 수 없습니다."
                    )
            else:
                print(f"\n📋 전체 작업 목록:")
            
            if not tasks:
                print("   작업이 없습니다.")
            else:
                for task in tasks:
                    status_icon = "✅" if task.status == TaskStatus.COMPLETED else "⏳"
                    print(f"   {status_icon} [{task.id}] {task.name}")
                    if task.description:
                        print(f"      📝 {task.description}")
            
            return StandardResponse.success({
                'tasks': tasks,
                'count': len(tasks)
            })
        
        elif action == "add":
            # 작업 추가
            if len(args) < 2:
                return StandardResponse.error(
                    ErrorType.VALIDATION_ERROR,
                    "사용법: task add <phase_id> <작업명> [설명]"
                )
            
            phase_id = args[0]
            name = args[1]
            description = args[2] if len(args) > 2 else ""
            
            # WorkflowManager로 위임
            task = wm.add_task(phase_id, name, description)
            
            if isinstance(task, dict) and task.get('success') is False:
                return StandardResponse(**task)
            
            print(f"✅ 작업이 추가되었습니다: [{task.id}] {task.name}")
            
            return StandardResponse.success({
                'task': task,
                'message': f"작업 '{task.name}'이(가) 추가되었습니다."
            })
        
        elif action == "done":
            # 작업 완료
            if not args:
                return StandardResponse.error(
                    ErrorType.VALIDATION_ERROR,
                    "사용법: task done <task_id>"
                )
            
            task_id = args[0]
            
            # WorkflowManager로 위임
            result = wm.complete_task(task_id)
            
            if isinstance(result, dict):
                return StandardResponse(**result)
            return result
        
        elif action == "remove":
            # 작업 삭제
            if not args:
                return StandardResponse.error(
                    ErrorType.VALIDATION_ERROR,
                    "사용법: task remove <task_id>"
                )
            
            task_id = args[0]
            
            # WorkflowManager로 위임
            result = wm.remove_task(task_id)
            
            if isinstance(result, dict):
                return StandardResponse(**result)
            return result
        
        elif action == "update":
            # 작업 수정
            if len(args) < 2:
                return StandardResponse.error(
                    ErrorType.VALIDATION_ERROR,
                    "사용법: task update <task_id> <name|description|status> <새 값>"
                )
            
            task_id = args[0]
            field = args[1]
            value = args[2] if len(args) > 2 else ""
            
            # WorkflowManager로 위임
            result = wm.update_task(task_id, field, value)
            
            if isinstance(result, dict):
                return StandardResponse(**result)
            return result
        
        else:
            return StandardResponse.error(
                ErrorType.VALIDATION_ERROR,
                f"알 수 없는 action: {action}. 사용 가능: list, add, done, remove, update"
            )
    
    except Exception as e:
        return StandardResponse.error(
            ErrorType.TASK_ERROR,
            f"작업 처리 중 오류: {str(e)}"
        )


# 명령줄 인터페이스
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="작업 관리")
    parser.add_argument('action', choices=['list', 'add', 'done', 'remove', 'update'],
                        help='수행할 작업')
    parser.add_argument('args', nargs='*', help='action에 따른 추가 인자')
    
    args = parser.parse_args()
    
    result = cmd_task(args.action, *args.args)
    
    if not result.success:
        print(f"❌ 오류: {result.error}")
        sys.exit(1)
